"""Account POST."""
import os
import uuid
import hashlib
import pathlib
from flask import request, redirect, url_for, session, abort
import insta485


def hash_password(password):
    """Hash password."""
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def verify_password(stored_password, input_password):
    """Verify password."""
    this_a, this_s, this_h = stored_password.split('$')
    hash_obj = hashlib.new(this_a)
    password_salted = this_s + input_password
    hash_obj.update(password_salted.encode('utf-8'))
    input_hash = hash_obj.hexdigest()
    return this_h == input_hash


def login_operation(req, connection, target_url):
    """Login operation."""
    username = req.form['username']
    this_pass = req.form['password']
    if not (username and this_pass):
        abort(400)
    result = connection.execute(
        "SELECT username, password "
        "FROM users WHERE username = ? ",
        (username, )
    ).fetchone()
    if result and verify_password(result['password'], this_pass):
        session['username'] = result['username']
    else:
        abort(403)
    return redirect(target_url)


def create_operation(req, connection, target_url):
    """Create operation."""
    username = req.form['username']
    this_pass = req.form['password']
    fullname = req.form['fullname']
    email = req.form['email']
    file = req.files['file']
    # check if any field is empty
    if not (username and this_pass and fullname and email and file):
        abort(400)

    stem = uuid.uuid4().hex
    suffix = pathlib.Path(file.filename).suffix.lower()
    uuid_basename = f"{stem}{suffix}"
    path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
    file.save(path)

    # check if username exist
    result = connection.execute(
        "SELECT 1 FROM users WHERE username = ? ",
        (username,)
    ).fetchone()
    if result:
        abort(409)
    hashed_pw = hash_password(this_pass)
    connection.execute(
        "INSERT INTO users (username, fullname, email, filename, password)\
        VALUES (?, ?, ?, ?, ?) ",
        (username, fullname, email, uuid_basename, hashed_pw)
    )
    session['username'] = username
    connection.commit()
    return redirect(target_url)


def delete_operation(connection, target_url):
    """Delete operation."""
    if 'username' not in session:
        abort(403)
    user_img = connection.execute(
        "SELECT filename FROM users WHERE username = ?",
        (session['username'],)
        ).fetchall()
    # make sure user_img is not None
    if user_img is not None:
        for filename_row in user_img:
            file_path = os.path.join(insta485.app.config['UPLOAD_FOLDER'],
                                     filename_row['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
    post_img = connection.execute(
        "SELECT filename FROM posts WHERE owner = ?",
        (session['username'],)
        ).fetchall()
    if post_img is not None:
        for filename_row in post_img:
            file_path = os.path.join(insta485.app.config['UPLOAD_FOLDER'],
                                     filename_row['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
    connection.execute(
        "DELETE FROM users WHERE username = ?",
        (session['username'],)
    )
    connection.commit()
    session.clear()
    return redirect(target_url)


def edit_account_operation(req, connection, target_url):
    """Edit account operation."""
    if 'username' not in session:
        abort(403)
    username = session['username']
    fullname = req.form['fullname']
    email = req.form['email']
    if not (fullname and email):
        abort(400)   # Bad request for empty comment
    if 'file' not in req.files:  # no uploaded picture
        connection.execute(
                           "UPDATE users "
                           "SET email = ?, fullname = ?"
                           "WHERE username = ?",
                           (email, fullname, username))
    else:
        file = req.files["file"]
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(file.filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        file.save(path)

        user_img = connection.execute(
            "SELECT filename FROM users WHERE username = ?",
            (session['username'],)
        ).fetchall()
        if user_img is not None:
            for filename_row in user_img:
                file_path = os.path.join(insta485.app.config['UPLOAD_FOLDER'],
                                         filename_row['filename'])
                if os.path.exists(file_path):
                    os.remove(file_path)
        connection.execute(
                           "UPDATE users "
                           "SET email = ?, fullname = ?, filename = ?"
                           "WHERE username = ?",
                           (email, fullname, uuid_basename, username))
    connection.commit()
    return redirect(target_url)


def update_password_operation(req, connection, target_url):
    """Update password operation."""
    if 'username' not in session:
        abort(403)
    username = session['username']
    result = connection.execute(
        "SELECT 1 AS placeholder, password "
        "FROM users WHERE username = ? ",
        (username, )
    ).fetchone()
    if not (req.form['password'] and req.form['new_password1']
            and req.form['new_password2']):
        abort(400)  # Bad request for empty fields
    if result and verify_password(result['password'], req.form['password']):
        if req.form['new_password1'] == req.form['new_password2']:
            connection.execute(
                "UPDATE users "
                "SET password = ? "
                "WHERE username = ?",
                (hash_password(req.form['new_password2']), username)
            )
        else:
            abort(401)
    else:
        abort(403)
    connection.commit()
    return redirect(target_url)


@insta485.app.route('/accounts/', methods=["POST"])
def handle_accounts():
    """Handle accounts."""
    target_url = request.args.get('target', '/')
    connection = insta485.model.get_db()
    operation = request.form.get('operation')
    if operation == 'login':
        return login_operation(request, connection, target_url)
    if operation == 'create':
        return create_operation(request, connection, target_url)
    if operation == 'delete':
        return delete_operation(connection, target_url)
    if operation == 'edit_account':
        return edit_account_operation(request, connection, target_url)
    if operation == 'update_password':
        return update_password_operation(request, connection, target_url)

    abort(400)  # Bad request for unsupported operations


@insta485.app.route('/accounts/logout/', methods=["POST"])
def handle_logout():
    """Handle logout."""
    session.clear()
    return redirect(url_for('show_login'))
