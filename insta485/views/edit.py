"""Edit GET."""
import flask
from flask import redirect, url_for, session
import insta485


@insta485.app.route('/accounts/edit/')
def show_edit():
    """Show edit."""
    connection = insta485.model.get_db()
    if 'username' not in session:
        return (redirect(url_for('show_login')))
    cur = connection.execute(
        "SELECT DISTINCT users.email, users.fullname,\
            users.filename AS user_f,\
            users.username "
        "FROM users "
        "WHERE users.username = ? ",
        (session['username'], )
    )
    user = cur.fetchone()

    return flask.render_template("edit.html",
                                 password_link=url_for('show_password'),
                                 delete_link=url_for('show_delete'),
                                 fullname=user['fullname'],
                                 email=user['email'],
                                 logname=user['username'],
                                 user_img_url=f"/uploads/{user['user_f']}")
