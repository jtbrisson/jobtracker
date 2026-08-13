from flask import Blueprint

bp = Blueprint("claims", __name__, url_prefix="/weeks")

from app.claims import routes  # noqa: E402,F401
