# =============================================================================
# MIV MOROGORO — auth.py
# =============================================================================
# Faili hili linashughulikia:
#   1. Kuweka nywila salama (hashing na bcrypt)
#   2. Login na logout
#   3. Kulinda routes — decorator @admin1_required, @admin_required
#
# DHANA MUHIMU — Password Hashing:
# ─────────────────────────────────
# Tusiandike nywila kama maandishi ya kawaida kwenye database!
# Mfano MBAYA:   db.save(password="admin123")   ← HATARI SANA
# Mfano NZURI:   db.save(password=bcrypt.hash("admin123"))
#                → "$2b$12$eImiTXuWVxfM37uY4JANjQ..."
#
# Hata msimamizi wa database akiiba data, hawezi kujua nywila halisi.
# bcrypt ni algorithm ya hashing inayotumika duniani kote kwa usalama.
#
# DHANA MUHIMU — Decorators:
# ──────────────────────────
# Decorator ni kazi inayofunika kazi nyingine.
# @admin1_required mbele ya route inamaanisha:
# "Kabla ya kuendesha hii, angalia kama mtumiaji ni admin1.
#  Kama sivyo, mrudishie ukurasa wa 'Hairuhusiwi'."
# =============================================================================

import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash, abort
from models import User, UserRole


# =============================================================================
# SEHEMU 1: Password Hashing
# =============================================================================

def hash_password(plain_password: str) -> str:
    """
    Badilisha nywila ya kawaida kuwa hash salama.

    Mfano:
        hash_password("admin123")
        → "$2b$12$eImiTXuWVxfM37uY4JANjQuu..."

    bcrypt inaongeza 'salt' kiotomatiki — maana hata nywila mbili
    zinazofanana zitakuwa na hash tofauti. Hii ni usalama zaidi.
    """
    salt = bcrypt.gensalt(rounds=12)
    # rounds=12 ni kiwango cha kawaida cha usalama wa IHK na industry
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def check_password(plain_password: str, hashed: str) -> bool:
    """
    Linganisha nywila iliyoandikwa na hash iliyohifadhiwa.
    Inarudisha True kama zinafanana, False kama hazifanani.

    Mfano:
        check_password("admin123", "$2b$12$eImi...") → True
        check_password("vibaya",   "$2b$12$eImi...") → False
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed.encode("utf-8")
    )


# =============================================================================
# SEHEMU 2: Session — Kukumbuka mtumiaji aliyeingia
# =============================================================================

def login_user(user: User) -> None:
    """
    Hifadhi taarifa za mtumiaji kwenye session baada ya login.
    Session ni kama 'kumbukumbu ya muda' ya Flask — inabaki hadi logout.

    Tunahifadhi:
      - user_id:   kujua ni nani
      - user_role: kujua ana ruhusa gani
      - username:  kuonyesha kwenye ukurasa
    """
    session.clear()
    session["user_id"]   = user.id
    session["user_role"] = user.role.value
    session["username"]  = user.username
    user.update_last_login()


def logout_user() -> None:
    """Futa session — mtumiaji ametoka"""
    session.clear()


def get_current_user() -> User | None:
    """
    Pata mtumiaji aliyeingia sasa hivi.
    Kama hakuna mtu aliyeingia, inarudisha None.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def is_logged_in() -> bool:
    """Je, kuna mtu aliyeingia?"""
    return "user_id" in session


# =============================================================================
# SEHEMU 3: Decorators za kulinda routes
# =============================================================================
# Jinsi ya kutumia:
#
#   @app.route("/reports")
#   @admin1_required          ← Ongeza hii kulinda route
#   def reports():
#       ...
#
# Kama mtumiaji si admin1, atapelekwa ukurasa wa login au "Hairuhusiwi".
# =============================================================================

def login_required(f):
    """
    Decorator: Mtumiaji lazima aingie kwanza.
    Kama hajaingia → redirect kwenye /login
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            flash("Tafadhali ingia kwanza.", "warning")
            return redirect(url_for("auth_bp.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """
    Decorator: Admin1 AU Admin2 wanaweza kuingia.
    Tenant hawezi. Mtu asiyeingia hawezi.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            flash("Tafadhali ingia kwanza.", "warning")
            return redirect(url_for("auth_bp.login"))
        role = session.get("user_role")
        if role not in (UserRole.ADMIN1.value, UserRole.ADMIN2.value):
            abort(403)  # Hairuhusiwi
        return f(*args, **kwargs)
    return decorated


def admin1_required(f):
    """
    Decorator: Admin1 TU anaweza kuingia.
    Inatumika kwa: ripoti, matumizi, mipangilio ya mfumo.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            flash("Tafadhali ingia kwanza.", "warning")
            return redirect(url_for("auth_bp.login"))
        role = session.get("user_role")
        if role != UserRole.ADMIN1.value:
            flash("Huna ruhusa ya sehemu hii.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# SEHEMU 4: Blueprint ya Login/Logout Routes
# =============================================================================

from flask import Blueprint, request, render_template
from database import db

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  /login  → Onyesha fomu ya login
    POST /login  → Angalia jina la mtumiaji na nywila
    """
    # Kama tayari ameingia, mrudishie dashboard
    if is_logged_in():
        return redirect(url_for("main_bp.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Tafuta mtumiaji kwenye database
        user = User.query.filter_by(username=username, is_active=True).first()

        if user and check_password(password, user.password_hash):
            # Nywila sahihi → ingia
            login_user(user)
            db.session.commit()

            # Mpeleke kwenye ukurasa unaofaa kulingana na role
            if user.is_admin1() or user.is_admin2():
                return redirect(url_for("main_bp.dashboard"))
            else:
                # Tenant → ukurasa wake mwenyewe tu
                return redirect(url_for("tenant_bp.my_receipts"))
        else:
            # Nywila mbaya — usiseme ni nini kilimshinda (usalama)
            flash("Jina la mtumiaji au nywila si sahihi.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Toa mtumiaji na mrudishie ukurasa wa login"""
    logout_user()
    flash("Umefanikiwa kutoka.", "info")
    return redirect(url_for("auth_bp.login"))


@auth_bp.route("/forbidden")
def forbidden():
    """Ukurasa wa 'Hairuhusiwi' — 403"""
    return render_template("errors/403.html"), 403
