"""Login GET."""
import flask
from flask import session, redirect, url_for
import insta485


@insta485.app.route('/accounts/login/')
def show_login():
    """Show login."""
    if 'username' in session:
        return redirect(url_for('show_index'))

    return flask.render_template("login.html",
                                 create_account_link=url_for('show_create'))
