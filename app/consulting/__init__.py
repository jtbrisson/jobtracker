from flask import Blueprint

bp = Blueprint("consulting", __name__, url_prefix="/consulting")

from app.consulting import routes  # noqa: E402,F401
