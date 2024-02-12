"""Passowrd POST."""
import flask
from flask import url_for, session
import insta485


@insta485.app.route('/accounts/password/')
def show_password():
    """Show password."""
    return flask.render_template("password.html",
                                 edit_link=url_for('show_edit'),
                                 logname=session['username'])
