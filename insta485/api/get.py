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
def get_posts():
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