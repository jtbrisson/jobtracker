from datetime import datetime
from functools import wraps

from flask import (
    redirect, url_for, session, render_template, current_app, flash, request,
)

from app.extensions import db, oauth
from app.models import User
from app.auth import bp


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


@bp.route("/login")
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.home"))
    return render_template("auth/login.html")


@bp.route("/login/github")
def login_github():
    redirect_uri = url_for("auth.auth_callback", _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


@bp.route("/callback")
def auth_callback():
    token = oauth.github.authorize_access_token()
    userinfo = token.get("userinfo")
    if not userinfo:
        # GitHub doesn't include userinfo in token response, fetch it via /user endpoint
        resp = oauth.github.get("/user")
        userinfo = resp.json()
    
    github_username = (userinfo.get("login") or "").lower()
    allowed = current_app.config.get("ALLOWED_GITHUB_USERNAMES") or []

    if allowed and github_username not in allowed:
        flash(f"GitHub user '{github_username}' is not authorized to use this app.", "error")
        return redirect(url_for("auth.login"))

    # Use email as unique identifier, fall back to username if email not available
    email = (userinfo.get("email") or f"{github_username}@github.local").lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email)
        db.session.add(user)

    user.name = userinfo.get("name") or github_username
    user.github_username = github_username
    user.avatar_url = userinfo.get("avatar_url")
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.name
    flash(f"Welcome back, {user.name or user.email}!", "success")
    return redirect(url_for("dashboard.home"))


@bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login"))
