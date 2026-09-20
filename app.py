# =============================================================================
# MIV MOROGORO — app.py
# =============================================================================
# Hii ndiyo mlango mkuu wa mfumo wetu.
# Ukiendesha:  python app.py
# Mfumo utaanza na utapatikana kwenye:  http://localhost:5000
# =============================================================================

import os
from flask import Flask
from database import init_db
from auth     import auth_bp


def create_app():
    """
    Application Factory Pattern.
    Badala ya kuunda app moja kuu, tunaifanya kama 'kiwanda'.
    Hii inafanya iwe rahisi zaidi kujaribu (testing) na kupanua.
    """
    app = Flask(__name__)

    # ── Mipangilio (Configuration) ────────────────────────────────────────
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "miv-morogoro-dev-key-badilisha-production"
        # ⚠️ Kwenye production: weka kwenye environment variable
        # export SECRET_KEY="nywila-ngumu-sana-ya-nasibu"
    )

    # Database: SQLite kwa maendeleo, PostgreSQL kwa production
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///miv_morogoro.db"
        # Faili la database litaundwa hapa: miv_morogoro.db
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = False
    # SQLALCHEMY_ECHO=True ukitaka kuona SQL inayoundwa (debugging)

    # ── Anza Database ─────────────────────────────────────────────────────
    init_db(app)

    # ── Sajili Blueprints (Sehemu za mfumo) ──────────────────────────────
    # Blueprint ni "kikundi" cha routes zinazohusiana.
    # Tunazigawanya ili code iwe nadhifu na rahisi kutafuta.

    from auth         import auth_bp
    # Sprint 2 tutaongeza hizi:
    # from routes.main    import main_bp
    # from routes.tenants import tenant_bp
    # from routes.payments import payment_bp
    # from routes.reports  import reports_bp

    app.register_blueprint(auth_bp)

    # ── Kurasa za makosa ──────────────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    return app


# =============================================================================
# Anza mfumo
# =============================================================================

if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=True,    # Onyesha makosa kwenye browser (maendeleo tu!)
        host="0.0.0.0",
        port=5000
    )
    # ⚠️ debug=True LAZIMA iwe False kwenye production!
