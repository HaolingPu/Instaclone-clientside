"""Auth GET."""
from flask import session, abort
import insta485


@insta485.app.route('/accounts/auth/')
def show_auth():
    """Show auth."""
    if 'username' in session:
        return '', 200

    abort(403)
