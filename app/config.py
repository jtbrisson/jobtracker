import os
from datetime import date


def _env_bool(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # --- Database ---
    # Render provides DATABASE_URL like postgres://... ; SQLAlchemy 1.4+/2.x wants postgresql://
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "instance", "jobtracker.db"
    ))
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth (GitHub OAuth) ---
    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
    # Comma-separated list of the only GitHub usernames allowed to log in.
    ALLOWED_GITHUB_USERNAMES = [
        u.strip().lower()
        for u in os.environ.get("ALLOWED_GITHUB_USERNAMES", "").split(",")
        if u.strip()
    ]

    # --- File storage (S3-compatible: Cloudflare R2, AWS S3, etc.) ---
    S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "")  # e.g. https://<account_id>.r2.cloudflarestorage.com
    S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID", "")
    S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY", "")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "job-tracker-files")
    S3_REGION = os.environ.get("S3_REGION", "auto")
    # Presigned URL expiry for downloads, in seconds (default 1 hour)
    S3_PRESIGN_EXPIRY = int(os.environ.get("S3_PRESIGN_EXPIRY", "3600"))

    # --- Unemployment claim / benefit year settings ---
    # First day (a Monday, matching CA EDD weekly claim weeks) of the benefit
    # year the claim-weeks table should start generating from.
    BENEFIT_YEAR_START = date.fromisoformat(
        os.environ.get("BENEFIT_YEAR_START", "2025-12-29")
    )
    BENEFIT_YEAR_WEEKS = int(os.environ.get("BENEFIT_YEAR_WEEKS", "53"))

    PREFERRED_URL_SCHEME = "https"


class DevConfig(Config):
    DEBUG = True
    PREFERRED_URL_SCHEME = "http"
    SESSION_COOKIE_SECURE = False


class ProdConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


def get_config():
    env = os.environ.get("FLASK_ENV", "production")
    return DevConfig if env == "development" else ProdConfig
