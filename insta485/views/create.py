"""Create GET."""
import flask
from flask import session, redirect, url_for
import insta485


@insta485.app.route('/accounts/create/')
def show_create():
    """Show create."""
    if 'username' in session:
        return redirect(url_for('show_edit'))

    return flask.render_template("create.html",
                                 login_link=url_for('show_login'))
