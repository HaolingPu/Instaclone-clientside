"""Insta485 REST API routes."""
import hashlib
import flask
from flask import request, session, abort
import insta485


@insta485.app.route('/api/v1/')
def get_resources():
    """Return a list of services available."""
    context = {
        "comments": "/api/v1/comments/",
        "likes": "/api/v1/likes/",
        "posts": "/api/v1/posts/",
        "url": "/api/v1/"
    }
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/posts/')
def get_page():
    """
    Return the 10 newest posts.

    The URL of the next page of posts is returned in next.
    Note that postid is an int, not a string.
    """
    if not check_auth():
        return flask.jsonify({"message": "Forbidden", "status_code": 403}), 403

    connection = insta485.model.get_db()
    logname = session['username']
    postid_lte = flask.request.args.get('postid_lte', type=int)

    # check for non-existing postid.
    if postid_lte:
        cur = connection.execute(
            "SELECT * FROM posts WHERE postid = ?",
            (postid_lte,))
        post = cur.fetchone()
        if post is None:
            abort(404)

    if postid_lte is None:
        cur = connection.execute(
            "SELECT MAX(postid) as id "
            "FROM posts p "
            "LEFT JOIN following f ON p.owner = f.username2 "
            "WHERE f.username1 = ? OR p.owner = ? ",
            (logname, logname))
        result = cur.fetchone()
        postid_lte = result['id'] if result else None
    size = flask.request.args.get('size', default=10, type=int)
    page = flask.request.args.get('page', default=0, type=int)

    if size <= 0 or page < 0:
        cur = {"message": "Bad Request", "status_code": 400}
        return flask.jsonify(cur), 400
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
    print("BEFORE")
    print("NUMBER OF POSTS ", len(posts))
    # print("PAGE ", page)
    if len(posts) >= size:
        next_url = f"/api/v1/posts/?size={size}&page={page+1}"
        print("AFTER")
        print("PAGE ", page)
        if postid_lte:
            next_url += f"&postid_lte={postid_lte}"
    results = []
    for post in posts:
        results.append({"postid": post['postid'],
                        "url": f"/api/v1/posts/{post['postid']}/"})
    exact_request_url = "/api/v1/posts/"
    if request.query_string:
        exact_request_url += f"?{request.query_string.decode('utf-8')}"
    print("NEXTURL ", next_url)
    context = {
        "next": next_url,
        "results": results,
        "url": exact_request_url,
    }

    return flask.jsonify(**context), 200


def check_auth():
    """Check the auth."""
    connection = insta485.model.get_db()
    if 'username' in session:
        return True

    auth = flask.request.authorization
    if auth is None:
        return False
    username = auth["username"]
    password = auth["password"]
    if not username or not password:
        return False

    cur = connection.execute(
        "SELECT password FROM users WHERE username = ?", (username,)
    )
    result = cur.fetchone()
    if result is not None:
        password_string = result['password']
        if verify_password(password_string, password):
            session['username'] = username
            return True
    return False


def verify_password(stored_password, input_password):
    """Verify password."""
    algorithm, salt, stored_hash = stored_password.split('$')
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + input_password
    hash_obj.update(password_salted.encode('utf-8'))
    input_hash = hash_obj.hexdigest()
    return stored_hash == input_hash


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/')
def get_post(postid_url_slug):
    """Return post on postid."""
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
    postimg = owner["filename"]

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
    likethis = False
    likeurl = None
    cur = cur.fetchone()
    if cur:
        likethis = True
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
        cur = comment["commentid"]
        comment["url"] = f"/api/v1/comments/{cur}/"
        cur = comment["owner"]
        comment["ownerShowUrl"] = f"/users/{cur}/"

    context = {
        "comments": comments,
        "comments_url": f"/api/v1/comments/?postid={postid_url_slug}",
        "created": owner["created"],
        "imgUrl": f"/uploads/{postimg}",
        "likes": {
            "lognameLikesThis": likethis,
            "numLikes": numlike,
            "url": likeurl
        },
        "owner": ownerusername,
        "ownerImgUrl": f"/uploads/{ownerimg}",
        "ownerShowUrl": f"/users/{ownerusername}/",
        "postShowUrl": f"/posts/{postid_url_slug}/",
        "postid": postid_url_slug,
        "url": f"/api/v1/posts/{postid_url_slug}/"
    }
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/likes/<int:likeid>/', methods=['DELETE'])
def delete_likes(likeid):
    """Delete the like."""
    print("I am in DELETE likes")
    # check authorization
    if check_auth() is False:
        return flask.jsonify({}), 403
    logname = session['username']
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT DISTINCT owner FROM likes WHERE likeid = ?",
        (likeid,)
    ).fetchone()
    if cur is None:
        print("error here?")
        return flask.jsonify({}), 404
    if cur['owner'] != logname:
        return flask.jsonify({}), 403
    connection.execute(
            "DELETE FROM likes WHERE likeid = ?",
            (likeid,)
        )
    connection.commit()
    return flask.jsonify({}), 204


@insta485.app.route('/api/v1/likes/', methods=['POST'])
def post_like():
    """Post the like."""
    if check_auth() is False:
        return flask.jsonify({}), 403

    logname = session['username']
    connection = insta485.model.get_db()
    postid = flask.request.args['postid']
    # check if postid exist / out of range
    cur = connection.execute(
        "SELECT * FROM posts WHERE postid = ?",
        (postid, )
    ).fetchone()
    if cur is None:
        return flask.jsonify({}), 404
    # check if the like already existed
    cur = connection.execute(
        "SELECT * FROM likes WHERE owner = ? AND postid = ?",
        (logname, postid)
    ).fetchone()
    if cur is not None:
        context = {
            "likeid": cur['likeid'],
            "url": f"/api/v1/likes/{cur['likeid']}/",
        }
        return flask.jsonify(**context), 200
    cur = connection.execute(
        "INSERT INTO likes (owner, postid) VALUES (?, ?)",
        (logname, postid)
    ).fetchone()
    connection.commit()
    # find the likeid

    cur = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()
    context = {
        "likeid": cur['last_insert_rowid()'],
        "url": f"/api/v1/likes/{cur['last_insert_rowid()']}/",
    }
    return flask.jsonify(**context), 201


# delete comments
@insta485.app.route('/api/v1/comments/<int:commentid>/', methods=['DELETE'])
def delete_comments(commentid):
    """Delete the comment."""
    if not check_auth():
        return flask.jsonify({"message": "Forbidden", "status_code": 403}), 403
    logname = session['username']
    connection = insta485.model.get_db()
    comment = connection.execute(
        "SELECT * FROM comments WHERE commentid = ?", (commentid, )
    ).fetchone()
    print(comment)
    if comment is None:
        return flask.jsonify({}), 404
    owner = comment['owner']
    if owner != logname:
        return flask.jsonify({}), 403
    connection.execute(
        "DELETE FROM comments WHERE commentid = ?", (commentid, )
    )
    connection.commit()
    return flask.jsonify({}), 204


@insta485.app.route('/api/v1/comments/', methods=['POST'])
def post_comment():
    """Post the comment."""
    if check_auth() is False:
        return flask.jsonify({}), 403
    logname = session['username']
    connection = insta485.model.get_db()
    postid = flask.request.args['postid']
    # check if postid exist / out of range
    cur = connection.execute(
        "SELECT * FROM comments WHERE postid = ?",
        (postid, )
    ).fetchone()
    if cur is None:
        return flask.jsonify({}), 404
    # insert
    text = flask.request.json.get("text", None)
    cur = connection.execute(
        "INSERT INTO comments (owner, postid, text) VALUES (?, ?, ?)",
        (logname, postid, text)
    ).fetchone()
    connection.commit()
    # get last row id
    cur = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()
    context = {
        "commentid": cur['last_insert_rowid()'],
        "lognameOwnsThis": True,
        "owner": logname,
        "ownerShowUrl": "/users/{logname}/",
        "text": text,
        "url": f"/api/v1/comments/{cur['last_insert_rowid()']}/"
    }
    return flask.jsonify(**context), 201
