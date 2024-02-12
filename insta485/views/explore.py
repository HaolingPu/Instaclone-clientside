"""Explore GET."""
import flask
from flask import session, redirect, url_for
import insta485


@insta485.app.route('/explore/')
def show_explore():
    """Display /explore/ route."""
    # Connect to database
    if 'username' not in session:
        return (redirect(url_for('show_login')))
    # Query database
    logname = session['username']
    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT DISTINCT username, filename AS img_url FROM users "
        "WHERE username != ? AND username NOT IN "
        "(SELECT username2 FROM following WHERE "
        "username1 = ? ) ",
        (logname, logname,)
    )

    context = {"logname": logname,
               "not_following": cur.fetchall()  # is an arrary of dictionaries
               }
    print(context)
    return flask.render_template("explore.html", **context)
