"""
Insta485 index (main) view.

URLs include:
/
"""
import os
import arrow
import flask
from flask import send_from_directory, abort
from flask import request, redirect, url_for, session
import insta485


@insta485.app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Upload file directory."""
    if 'username' not in session:
        abort(403)
    # DNE
    if os.path.exists('/uploads/<path:filename>'):
        abort(404)
    uploads_dir = insta485.app.config['UPLOAD_FOLDER']
    return send_from_directory(uploads_dir, filename)


likes = {}  # key: postid, value: set of usernames who liked the post


@insta485.app.route('/likes/', methods=['POST'])
def handle_like():
    """Handle like."""
    if 'username' not in session:
        abort(401)  # User must be logged in to like or unlike a post

    target_url = request.args.get('target', '/')
    operation = request.form['operation']
    postid = request.form['postid']
    username = session['username']
    connection = insta485.model.get_db()

    if operation == 'like':
        # Check if the user has already liked the post
        existing_like = connection.execute(
            "SELECT 1 FROM likes WHERE owner = ? AND postid = ?",
            (username, postid)
        ).fetchone()
        if existing_like:
            abort(409)  # Conflict
        else:
            connection.execute(
                "INSERT INTO likes (owner, postid) VALUES (?, ?)",
                (username, postid)
            )
            connection.commit()
    elif operation == 'unlike':
        # Check if the user has liked the post before
        existing_like = connection.execute(
            "SELECT 1 FROM likes WHERE owner = ? AND postid = ?",
            (username, postid)
        ).fetchone()
        if not existing_like:
            abort(409)  # Conflict
        else:
            connection.execute(
                "DELETE FROM likes WHERE owner = ? AND postid = ?",
                (username, postid)
            )
            connection.commit()
    else:
        abort(400)  # Bad request for unsupported operations

    return redirect(target_url if target_url else url_for('show_index'))


@insta485.app.route('/comments/', methods=['POST'])
def handle_comment():
    """Handle comment."""
    if 'username' not in session:
        abort(401)  # User must be logged in to create or delete comments

    target_url = request.args.get('target', '/')
    operation = request.form['operation']
    username = session['username']
    connection = insta485.model.get_db()

    if operation == 'create':
        postid = request.form['postid']
        # Trim whitespace from the comment text
        text = request.form['text'].strip()
        if not text:
            abort(400)  # Bad request for empty comment

        connection.execute(
            "INSERT INTO comments (owner, postid, text) VALUES (?, ?, ?)",
            (username, postid, text)
        )
        connection.commit()
    elif operation == 'delete':
        commentid = request.form['commentid']

        # Verify ownership before deletion
        owner_check = connection.execute(
            "SELECT owner FROM comments WHERE commentid = ?",
            (commentid,)
        ).fetchone()
        if owner_check is None or owner_check['owner'] != username:
            abort(403)  # Forbidden to delete comments not owned by the user

        connection.execute(
            "DELETE FROM comments WHERE commentid = ?",
            (commentid,)
        )
        connection.commit()
    else:
        abort(400)  # Bad request for unsupported operations

    return redirect(target_url if target_url else url_for('show_index'))


@insta485.app.route('/')
def show_index():
    """Display / route."""
    # Connect to database
    connection = insta485.model.get_db()
    if 'username' not in session:
        return redirect(url_for('show_login'))

    logname = session['username']
    cur = connection.execute(
        "SELECT * "
        "FROM users "
        "WHERE username = ?",
        (logname, )
    )

    # cur = connection.execute(
    #     "SELECT * "
    #     "FROM posts "
    #     "WHERE owner = ?",
    #     (logname, )
    # )
    # posts = cur.fetchall()

    cur = connection.execute(
        "SELECT DISTINCT posts.filename AS post_filename, posts.postid,\
            posts.owner, posts.created, \
            users.filename AS user_filename "
        "FROM posts "
        "JOIN users ON posts.owner = users.username "
        "LEFT JOIN following ON posts.owner = following.username2 "
        "WHERE following.username1 = ? OR posts.owner = ? "
        "ORDER BY posts.postid DESC",
        (logname, logname)
    )
    posts = cur.fetchall()

    context_posts = []
    for p in posts:
        post_dict = {}
        post_dict["postid"] = p['postid']
        post_dict["owner"] = p['owner']

        # cur = connection.execute("SELECT filename "
        #                          "FROM users "
        #                          "WHERE username = ?",
        #                          (post_dict['owner'], ))
        # ownerimg_url = cur.fetchone()

        post_dict["owner_img_url"] = p['user_filename']
        post_dict["img_url"] = p['post_filename']
        post_creation_time = arrow.get(p['created'])
        post_dict["timestamp"] = post_creation_time.humanize()

        cur = connection.execute("SELECT COUNT(*) AS like_count "
                                 "FROM likes "
                                 "WHERE postid = ?",
                                 (post_dict['postid'],))
        likes_count = cur.fetchone()['like_count']
        post_dict['likes'] = likes_count

        # check like button or unlike
        cur = connection.execute(
            "SELECT 1 FROM likes WHERE postid = ? AND owner = ? ",
            (post_dict['postid'], logname)
        )
        result = cur.fetchone()
        liked = bool(result) if result else False  # Corrected logic
        post_dict['liked'] = liked

        post_dict['comments'] = []
        cur = connection.execute("SELECT* "
                                 "FROM comments "
                                 "WHERE postid = ?",
                                 (post_dict['postid'], ))
        comments = cur.fetchall()
        for c in comments:
            post_dict["comments"].append({
                "owner": c['owner'],
                "text": c['text']
            })

        context_posts.append(post_dict)

    # Add database info to context
    context = {"logname": logname,
               "posts": context_posts
               }
    return flask.render_template("index.html", **context)
