import flask
import insta485
import pathlib
import uuid
import arrow
import hashlib
from flask import request, redirect, url_for, session, abort

@insta485.app.route('/api/v1/')
def get_resources():
    """Return a list of services available"""
    context = {
        "comments": "/api/v1/comments/",
        "likes": "/api/v1/likes/",
        "posts": "/api/v1/posts/",
        "url": "/api/v1/"
    }
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/posts/')
def get_page():
    """Return the 10 newest posts. 
    The URL of the next page of posts is returned in next. 
    Note that postid is an int, not a string."""

    if 'username' not in session:
        auth = flask.request.authorization
        if auth:
            username = auth["username"]
            password = auth["password"]
        if not auth or not check_auth(username, password):
            return flask.jsonify({"message": "Forbidden", "status_code": 403}), 403
        session['username'] = username

    connection = insta485.model.get_db()
    logname = session['username']
    postid_lte = flask.request.args.get('postid_lte', type=int)

    #check for non-existing postid.
    if postid_lte:
        cur = connection.execute("SELECT * FROM posts WHERE postid = ?", (postid_lte,))
        post = cur.fetchone()
        if post is None:
            abort(404) 

    if postid_lte is None:
        cur = connection.execute(
            "SELECT MAX(postid) as id "
            "FROM posts p "
            "LEFT JOIN following f ON p.owner = f.username2 "
            "WHERE f.username1 = ? OR p.owner = ? ",
            (logname,logname))
        result = cur.fetchone()
        postid_lte = result['id'] if result else None
    size = flask.request.args.get('size', default=10, type=int)
    page = flask.request.args.get('page', default=0, type=int)

    if size <= 0 or page < 0:
        return flask.jsonify({"message": "Bad Request", "status_code": 400}), 400
    
    base_query = """
    SELECT DISTINCT p.postid, p.filename, p.owner, p.created
    FROM posts p
    LEFT JOIN following f ON p.owner = f.username2
    WHERE (f.username1 = ? OR p.owner = ?
    )
    """

    params = [logname, logname]
    if postid_lte is not None:
        base_query += " AND p.postid <= ?"
        params.append(postid_lte)

    base_query += " ORDER BY p.postid DESC"
    base_query += " LIMIT ? OFFSET ?"
    params.extend([size, page * size])

    posts = connection.execute(base_query, params).fetchall()

    next_url = ""
    if len(posts) == size:
        next_url = f"/api/v1/posts/?size={size}&page={page + 1}"
        if postid_lte:
            next_url += f"&postid_lte={postid_lte}"
   
    results = []
    for post in posts:
        results.append(
            {
            "postid":post['postid'],
            "url":f"/api/v1/posts/{post['postid']}/"
             }
            )
    exact_request_url = "/api/v1/posts/"
    if request.query_string:
        exact_request_url += f"?{request.query_string.decode('utf-8')}"

    context = {
        "next":next_url,
        "results":results,
        "url": exact_request_url,
    }

    return flask.jsonify(**context),200



def check_auth(username, password):
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT password FROM users WHERE username = ?", (username,)
    )
    result = cur.fetchone()
    if result is not None:
        password_string = result['password']
        if verify_password(password_string,password):
            return True
    return False



# def hash_password(password):
#     """Hash password."""
#     algorithm = 'sha512'
#     salt = uuid.uuid4().hex
#     hash_obj = hashlib.new(algorithm)
#     password_salted = salt + password
#     hash_obj.update(password_salted.encode('utf-8'))
#     password_hash = hash_obj.hexdigest()
#     password_db_string = "$".join([algorithm, salt, password_hash])
#     return password_db_string


def verify_password(stored_password, input_password):
    """Verify password."""
    algorithm, salt, stored_hash = stored_password.split('$')
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + input_password
    hash_obj.update(password_salted.encode('utf-8'))
    input_hash = hash_obj.hexdigest()
    return stored_hash == input_hash



# post_id
"""REST API for posts."""


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/')
def get_post(postid_url_slug):
    """Return post on postid.

    Example:
    {
      "created": "2017-09-28 04:33:28",
      "imgUrl": "/uploads/122a7d27ca1d7420a1072f695d9290fad4501a41.jpg",
      "owner": "awdeorio",
      "ownerImgUrl": "/uploads/e1a7c5c32973862ee15173b0259e3efdb6a391af.jpg",
      "ownerShowUrl": "/users/awdeorio/",
      "postShowUrl": "/posts/1/",
      "postid": 1,
      "url": "/api/v1/posts/1/"
    }
    """
    logname = ''
    if 'username' in flask.session:
      logname = flask.session["username"]
    else:
      # 验证authorization

      logname = flask.request.authorization["username"]

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT owner, created, filename "
        "FROM posts "
        "WHERE postid == ?",
        (postid_url_slug, )
    )
    owner = cur.fetchone()
    if not owner:
      return flask.jsonify({"message": "Not Found", "status_code": 404}), 404
    
    cur = connection.execute(
        "SELECT filename "
        "FROM users "
        "WHERE username == ?",
        (owner["owner"], )
    )
    ownerimg = cur.fetchone()["filename"]

    cur = connection.execute(
        "SELECT * "
        "FROM likes "
        "WHERE owner == ? AND postid == ?",
        (logname, postid_url_slug,)
    )
    LikeThis = False
    likeurl = None
    cur = cur.fetchone()
    if cur:
      LikeThis = True
      likeid = cur["likeid"]
      likeurl = f"/api/v1/likes/{likeid}/"

    cur = connection.execute(
        "SELECT * "
        "FROM likes "
        "WHERE postid == ?",
        (postid_url_slug, )
    )
    numlike = len(cur.fetchall())
    ownerusername = owner["owner"]

    # comments
    cur = connection.execute(
        "SELECT commentid, owner, text "
        "FROM comments "
        "WHERE postid == ?",
        (postid_url_slug, )
    )

    comments = cur.fetchall()
    # comments = [{
    #   "commentid": 1,
    #   "owner": "awdeorio",
    #   "text": "#chickensofinstagram",
    # }, {...}, ...]


    #  need to add:
    #  "lognameOwnsThis": true,
    #  "url": "/api/v1/comments/1/"
    #  "ownerShowUrl": "/users/awdeorio/"

    for comment in comments:
      if logname == comment["owner"]:
        comment["lognameOwnsThis"] = True
      else: 
        comment["lognameOwnsThis"] = False
      cd = comment["commentid"]
      comment["url"] = f"/api/v1/comments/{cd}/"
      osu = comment["owner"]
      comment["ownerShowUrl"] = f"/users/{osu}/"

    context = {
      "comments": comments,
      "comments_url": f"/api/v1/comments/?postid={postid_url_slug}", 
      "created": owner["created"] ,
      "imgUrl": owner["filename"],
      "likes": {
        "lognameLikesThis": LikeThis,
        "numLikes": numlike,
        "url": likeurl
      },
      "owner": ownerusername,
      "ownerImgUrl": ownerimg,
      "ownerShowUrl": f"/users/{ownerusername}/",
      "postShowUrl": f"/posts/{postid_url_slug}/",
      "postid": postid_url_slug,
      "url": f"/api/v1/posts/{postid_url_slug}/"
    }
    return flask.jsonify(**context)