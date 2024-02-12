"""delete GET."""
import flask
from flask import session
import insta485


@insta485.app.route('/accounts/delete/')
def show_delete():
    """Show delete."""
    return flask.render_template("delete.html",
                                 logname=session['username'])
