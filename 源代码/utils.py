from __future__ import annotations

from datetime import datetime
from functools import wraps

from flask import abort, flash, redirect, session, url_for

from extensions import db
from models import User


def parse_date(value: str):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def get_current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not get_current_user():
            flash("请先登录系统。", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("请先登录系统。", "warning")
                return redirect(url_for("login"))
            if user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    return decorator
