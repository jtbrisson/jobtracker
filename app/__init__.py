import os

from dotenv import load_dotenv

load_dotenv()  # no-op in production where real env vars are already set

from flask import Flask

from app.config import get_config
from app.extensions import db, migrate, oauth


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object or get_config())

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)

    oauth.register(
        name="github",
        client_id=app.config["GITHUB_CLIENT_ID"],
        client_secret=app.config["GITHUB_CLIENT_SECRET"],
        access_token_url="https://github.com/login/oauth/access_token",
        access_token_params=None,
        authorize_url="https://github.com/login/oauth/authorize",
        authorize_params=None,
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )

    from app.auth import bp as auth_bp
    from app.dashboard import bp as dashboard_bp
    from app.claims import bp as claims_bp
    from app.applications import bp as applications_bp
    from app.consulting import bp as consulting_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(consulting_bp)

    @app.template_filter("money")
    def money_filter(value):
        try:
            return f"${float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return value

    @app.template_filter("dateonly")
    def dateonly_filter(value, fmt="%b %-d, %Y"):
        if not value:
            return ""
        try:
            return value.strftime(fmt)
        except ValueError:
            # %-d isn't supported on some platforms (Windows); fall back.
            return value.strftime("%b %d, %Y")

    @app.context_processor
    def inject_globals():
        from flask import session
        return {"current_user_email": session.get("user_email"), "current_user_name": session.get("user_name")}

    @app.cli.command("seed-weeks")
    def seed_weeks_command():
        """Generate the CA EDD claim-week rows from BENEFIT_YEAR_START."""
        from app.claims.utils import generate_weeks
        created = generate_weeks(
            app.config["BENEFIT_YEAR_START"], app.config["BENEFIT_YEAR_WEEKS"]
        )
        print(f"Created {created} claim week(s).")

    return app
