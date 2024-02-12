"""Followers GET."""
import flask
from flask import abort, session, url_for, redirect
import insta485


@insta485.app.route('/users/<user_url_slug>/followers/')
def show_followers(user_url_slug):
    """Display /users/<user_url_slug>/followers/ route."""
    # Connect to database
    connection = insta485.model.get_db()
    if 'username' not in session:
        return redirect(url_for('show_login'))
    # Query database
    logname = session['username']
    the_user = connection.execute(
        "SELECT * "
        "FROM users "
        "WHERE username = ?",
        (user_url_slug, )
    ).fetchone()
    # if username not in database
    if the_user is None:
        abort(404)

    cur = connection.execute(
        "SELECT DISTINCT following.username1, following.username2,\
            users.filename AS user_filename "
        "FROM following "
        "JOIN users ON following.username1 = users.username "
        "WHERE following.username2 = ? ",
        (user_url_slug, )
    )
    followers = cur.fetchall()
    context_followers = []  # is an arrary containing many dictionaries
    for p in followers:
        followers_dict = {}
        followers_dict["username"] = p['username1']
        followers_dict["user_img_url"] = f"/uploads/{p['user_filename']}"

        # check following or not following
        cur = connection.execute(
            "SELECT 1 FROM following WHERE username1 = ? AND username2 = ? ",
            (logname, followers_dict['username'])
        )
        result = cur.fetchone()
        followed = bool(result) if result else False  # Corrected logic
        followers_dict["logname_follows_username"] = followed
        context_followers.append(followers_dict)

    context = {"logname": logname,
               "followers": context_followers}

    return flask.render_template("followers.html", **context)
