"""Post."""
import pathlib
import uuid
import arrow
from flask import request, redirect, url_for, session
import flask
import insta485


@insta485.app.route('/posts/<post_id>/')
def show_posts(post_id):
    """Display / route."""
    # Connect to database
    connection = insta485.model.get_db()
    if 'username' not in session:
        return (redirect(url_for('show_login')))
    logname = session['username']
    # Query database
    cur = connection.execute(
        "SELECT DISTINCT posts.filename AS post_filename,\
            posts.owner, posts.created, \
            users.filename AS user_filename "
        "FROM posts "
        "JOIN users ON posts.owner = users.username "
        "WHERE posts.postid = ?",
        (post_id, )
    )
    p = cur.fetchone()

    contexts = {}
    contexts["logname"] = logname
    contexts["postid"] = post_id
    contexts["owner"] = p['owner']
    # print(p['user_filename'], " " ,p['post_filename'])
    # contexts["owner_img_url"] = f"/uploads/{p['user_filename']}"
    # print(contexts["owner_img_url"])
    # contexts["img_url"] = f"/uploads/{p['post_filename']}"

    contexts["owner_img_url"] = p['user_filename']
    contexts["img_url"] = p['post_filename']

    post_creation_time = arrow.get(p['created'])
    contexts["timestamp"] = post_creation_time.humanize()
    cur = connection.execute("SELECT COUNT(*) AS like_count "
                             "FROM likes "
                             "WHERE postid = ?",
                             (post_id,))
    likes_count = cur.fetchone()['like_count']
    p['likes'] = likes_count

    # check like button or unlike
    cur = connection.execute(
        "SELECT * FROM likes WHERE postid = ?  ",
        (post_id, )
    )
    result = cur.fetchall()
    liked = len(result)
    contexts['likes'] = liked

    p['comments'] = []
    cur = connection.execute("SELECT* "
                             "FROM comments "
                             "WHERE postid = ?",
                             (post_id, ))
    comments = cur.fetchall()

    cur = connection.execute(
        "SELECT * FROM likes WHERE postid = ? AND owner = ?",
        (post_id, logname,)
    )

    if not cur.fetchone():
        contexts["liked"] = False
    else:
        contexts["liked"] = True

    contexts["comments"] = comments

    # Add database info to context
    return flask.render_template("post.html", **contexts)


@insta485.app.route('/posts/', methods=['POST'])
def handle_post():
    """Handle post."""
    target_url = request.args.get('target', None)
    operation = request.form['operation']
    username = session['username']
    connection = insta485.model.get_db()

    if operation == 'create':
        fileobj = flask.request.files["file"]
        filename = fileobj.filename
        if not fileobj or filename == '':
            flask.abort(400, 'No file submitted or file is empty')

        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)
        connection.execute(
            "INSERT INTO posts (filename, owner) VALUES (?, ?)",
            (uuid_basename, username)
        )
    elif operation == 'delete':
        postid = request.form['postid']
        post = connection.execute(
            "SELECT * FROM posts WHERE postid = ?",
            (postid, )
        ).fetchone()
        if not post or post['owner'] != username:
            flask.abort(403, "Unauthorized to delete this post.")
        path = (pathlib.Path(insta485.app.config["UPLOAD_FOLDER"])
                / post['filename'])
        if path.exists():
            path.unlink()
        connection.execute(
            "DELETE FROM posts WHERE postid = ?",
            (postid, )
            )
    connection.commit()
    return flask.redirect(target_url if target_url
                          else url_for("show_user", user_url_slug=username))
