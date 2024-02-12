"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
from flask import redirect, url_for, session, abort
import insta485


@insta485.app.route('/users/<user_url_slug>/')
def show_user(user_url_slug):
    """Show user."""
    if 'username' not in session:
        return redirect(url_for('show_login'))
    # Connect to database
    connection = insta485.model.get_db()
    # Query database
    logname = session['username']

    if (connection.execute(
                            "SELECT * "
                            "FROM users "
                            "WHERE username = ?",
                            (user_url_slug, )).fetchone()) is None:

        abort(404)

    # number of followings
    cur = connection.execute(
        "SELECT username2 "
        "FROM following "
        "WHERE username1 == ?",
        (user_url_slug, )
    )

    cur = cur.fetchall()
    num_following = len(cur)

    # number of followers
    cur = connection.execute(
        "SELECT username1 "
        "FROM following "
        "WHERE username2 == ?",
        (user_url_slug, )
    )

    cur = cur.fetchall()
    num_followers = len(cur)

    # number of posts
    cur = connection.execute(
        "SELECT postid, filename "
        "FROM posts "
        "WHERE owner == ?",
        (user_url_slug, )
    )

    posts = cur.fetchall()
    total_posts = len(posts)
    for p in posts:
        p["img_url"] = p["filename"]

    # fullname
    cur = connection.execute(
        "SELECT fullname "
        "FROM users "
        "WHERE username == ?",
        (user_url_slug, )
    )

    cur = cur.fetchone()
    fullname_result = cur["fullname"]

    cur = connection.execute(
            "SELECT 1 FROM following WHERE username1 = ? AND username2 = ? ",
            (logname, user_url_slug)
        )
    result = cur.fetchone()
    followed = bool(result) if result else False  # Corrected logic

    context = {
               "logname": logname,
               "username": user_url_slug,
               "following": num_following,
               "followers": num_followers,
               "logname_follows_username": followed,
               "total_posts": total_posts,
               "fullname": fullname_result,
               "posts": posts
               }

    return flask.render_template("user.html", **context)
