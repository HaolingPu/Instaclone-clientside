"""Following."""
import flask
from flask import request, session, abort, url_for, redirect
import insta485


@insta485.app.route('/users/<user_url_slug>/following/')
def show_following(user_url_slug):
    """Display /users/<user_url_slug>/following/ route."""
    connection = insta485.model.get_db()
    if 'username' not in session:
        return redirect(url_for('show_login'))
    cur = connection.execute(
        "SELECT * "
        "FROM users "
        "WHERE username = ?",
        (user_url_slug, )
    )
    users = cur.fetchone()
    # if username not in database
    if users is None:
        abort(404)
    logname = session['username']

    cur = connection.execute(
        "SELECT DISTINCT following.username1, following.username2,\
            users.filename AS user_filename "
        "FROM following "
        "JOIN users ON following.username2 = users.username "
        "WHERE following.username1 = ? ",
        (user_url_slug, )
    )
    following = cur.fetchall()
    context_following = []
    for p in following:
        following_dict = {}
        following_dict["username"] = p['username2']
        following_dict["user_img_url"] = f"/uploads/{p['user_filename']}"

        # check following or not following
        cur = connection.execute(
            "SELECT 1 FROM following WHERE username1 = ? AND username2 = ? ",
            (logname, following_dict['username'])
        )
        result = cur.fetchone()
        followed = bool(result) if result else False  # Corrected logic
        following_dict["logname_follows_username"] = followed
        context_following.append(following_dict)

    context = {"logname": logname,
               "following": context_following
               }
    print(user_url_slug, "\n")
    print(context)
    return flask.render_template("following.html", **context)


@insta485.app.route('/following/', methods=['POST'])
def handle_following():
    """Handle following."""
    target_url = request.args.get('target', '/')
    operation = request.form['operation']
    username = flask.request.form['username']
    logname = session['username']
    connection = insta485.model.get_db()

    relationship = connection.execute(
        "SELECT * FROM following WHERE username1 = ? AND username2 = ?",
        (logname, username)
    ).fetchone()

    if operation == 'follow':
        if relationship:
            flask.abort(409)
        else:
            connection.execute(
                "INSERT INTO following (username1, username2) VALUES (?, ?)",
                (logname, username)
            )
    elif operation == 'unfollow':
        if not relationship:
            flask.abort(409)
        else:
            connection.execute(
                "DELETE FROM following WHERE username1 = ? AND username2 = ?",
                (logname, username))
    connection.commit()

    return flask.redirect(target_url if target_url
                          else flask.url_for("show_index"))
