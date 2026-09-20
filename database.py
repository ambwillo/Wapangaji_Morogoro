# =============================================================================
# MIV MOROGORO — database.py
# =============================================================================
# Faili hili linaunganisha mfumo wetu na database.
#
# Tunatumia SQLAlchemy — "ORM" (Object Relational Mapper).
# ORM maana: tunaandika Python, SQLAlchemy inabadilisha kuwa SQL.
#
# Mfano bila ORM (SQL mtupu):
#   cursor.execute("SELECT * FROM tenants WHERE is_active = 1")
#
# Mfano na ORM (SQLAlchemy):
#   Tenant.query.filter_by(is_active=True).all()
#
# Ni rahisi zaidi kusoma, kuandika, na kurekebisha makosa.
# =============================================================================

from flask_sqlalchemy import SQLAlchemy

# db ni kitu kimoja kinachotumika kwenye faili zote (models, routes, n.k.)
# Tunaunda hapa, tunaingiza kwenye app.py
db = SQLAlchemy()


def init_db(app):
    """
    Unganisha database na Flask app.
    Inaitwa mara moja kwenye app.py wakati wa kuanza mfumo.
    """
    db.init_app(app)
    with app.app_context():
        # Unda meza zote kama hazipo bado
        # Kwa production tutabadilisha hii na Flask-Migrate
        db.create_all()
        _seed_initial_data()


def _seed_initial_data():
    """
    Ingiza data ya awali kama database ni mpya.
    Hii inajaza:
      - Majengo mawili ya Morogoro
      - Vyumba vyote
      - Wapangaji wa kwanza
      - Akaunti ya admin1 na admin2

    Inaitwa mara moja tu — ukiwa tayari na data haiingii tena.
    """
    # Ili kuepuka import ya mzunguko (circular import),
    # tunaingiza models hapa ndani ya function
    from models import Building, Room, Tenant, User, UserRole
    from auth   import hash_password

    # Angalia kama tayari kuna data
    if Building.query.first():
        return  # Data ipo tayari — usiingize tena

    print("🌱 Inaingiza data ya awali ya Morogoro...")

    # ── Majengo ──────────────────────────────────────────────────────────
    kubwa = Building(
        name        = "Nyumba Kubwa",
        description = "Nyumba ya mbele yenye vyumba vinne. "
                      "Mpangaji wa sasa ana sebule, jiko, choo na bafu lake.",
        address     = "Morogoro, Tanzania"
    )
    ndogo = Building(
        name        = "Nyumba Ndogo",
        description = "Nyumba ya nyuma yenye vyumba vitatu. "
                      "Wapangaji wanashiriki choo, bafu na jiko.",
        address     = "Morogoro, Tanzania"
    )
    db.session.add_all([kubwa, ndogo])
    db.session.flush()  # Pata IDs kabla ya kuendelea

    # ── Vyumba — Nyumba Kubwa ─────────────────────────────────────────────
    rooms_kubwa = [
        Room(building_id=kubwa.id, room_number="Chumba 1 & 2",
             description="Vyumba vikubwa viwili pamoja na sebule, "
                         "jiko lake, choo lake na bafu lake.",
             monthly_rent=250_000, is_occupied=True,
             shared_facilities=False),
        Room(building_id=kubwa.id, room_number="Chumba 3",
             description="Chumba kimoja — wazi",
             monthly_rent=100_000, is_occupied=False,
             shared_facilities=False),
        Room(building_id=kubwa.id, room_number="Chumba 4",
             description="Chumba kimoja — wazi",
             monthly_rent=100_000, is_occupied=False,
             shared_facilities=False),
    ]

    # ── Vyumba — Nyumba Ndogo ─────────────────────────────────────────────
    rooms_ndogo = [
        Room(building_id=ndogo.id, room_number="Chumba 1 & 2",
             description="Vyumba viwili — wanashiriki bafu/choo/jiko",
             monthly_rent=150_000, is_occupied=True,
             shared_facilities=True),
        Room(building_id=ndogo.id, room_number="Chumba cha kati",
             description="Chumba cha kati — wanashiriki bafu/choo/jiko",
             monthly_rent=80_000, is_occupied=True,
             shared_facilities=True),
        Room(building_id=ndogo.id, room_number="Chumba kimoja",
             description="Chumba kidogo — wanashiriki bafu/choo/jiko",
             monthly_rent=60_000, is_occupied=True,
             shared_facilities=True),
    ]

    all_rooms = rooms_kubwa + rooms_ndogo
    db.session.add_all(all_rooms)
    db.session.flush()

    # ── Wapangaji ─────────────────────────────────────────────────────────
    from datetime import date
    tenants = [
        Tenant(room_id=rooms_kubwa[0].id, name="Amani Mwamba",
               phone="0712000001", start_date=date(2024, 6, 1)),
        Tenant(room_id=rooms_ndogo[0].id, name="Juma Salehe",
               phone="0712000002", start_date=date(2024, 9, 1)),
        Tenant(room_id=rooms_ndogo[1].id, name="Fatuma Ali",
               phone="0712000003", start_date=date(2025, 1, 1)),
        Tenant(room_id=rooms_ndogo[2].id, name="Hassan Omari",
               phone="0712000004", start_date=date(2025, 3, 1)),
    ]
    db.session.add_all(tenants)
    db.session.flush()

    # ── Watumiaji wa mfumo ────────────────────────────────────────────────
    admin1 = User(
        username      = "admin",
        password_hash = hash_password("admin123"),
        # ⚠️ BADILISHA NYWILA hii kabla ya kupeleka mtandaoni!
        role          = UserRole.ADMIN1,
        full_name     = "Msimamizi Mkuu",
    )
    admin2 = User(
        username      = "hassan",
        password_hash = hash_password("hassan123"),
        # ⚠️ BADILISHA NYWILA hii pia!
        role          = UserRole.ADMIN2,
        full_name     = "Hassan (Msimamizi Msaidizi)",
    )
    db.session.add_all([admin1, admin2])
    db.session.commit()

    print("✅ Data ya awali imeingizwa!")
    print("   → Admin1:  username='admin'  password='admin123'")
    print("   → Admin2:  username='hassan' password='hassan123'")
    print("   ⚠️  Badilisha nywila hizi kabla ya kupeleka mtandaoni!")
