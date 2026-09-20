# =============================================================================
# MIV MOROGORO — models.py
# =============================================================================
# Hii ndiyo "moyo" wa mfumo wetu. Kila kitu kinachohifadhiwa kwenye database
# kinaanzia hapa. Tunatumia SQLAlchemy ORM — maana Python inaandika SQL
# kwa ajili yetu. Sisi tunaandika Python tu.
#
# MUUNDO WA DATABASE (ER Model):
#
#   Building ──< Room ──< Tenant ──< Payment
#                              └──< (room pia ina history ya wapangaji)
#   Building ──< Expense
#   User  (admin1, admin2 — hawana uhusiano na Tenant table)
#
# =============================================================================

from datetime import datetime, date
from enum import Enum as PyEnum

from database import db   # tutaunda database.py baadaye


# =============================================================================
# ENUMS — badala ya kuandika "paid"/"due"/"late" kama strings zisizo salama,
# tunatumia Enum. Python itakusaidia ukikosea spelling.
# =============================================================================

class PaymentStatus(PyEnum):
    """Hali ya malipo ya kodi"""
    PAID = "paid"         # Amelipa
    DUE  = "due"          # Bado hajalipa (bado ndani ya mwezi)
    LATE = "late"         # Deni — mwezi umepita, hajalipa


class UserRole(PyEnum):
    """Aina ya mtumiaji wa mfumo"""
    ADMIN1  = "admin1"   # Msimamizi mkuu — upatikanaji kamili
    ADMIN2  = "admin2"   # Msimamizi msaidizi — upatikanaji mdogo
    TENANT  = "tenant"   # Mpangaji — anaona risiti yake tu


class ExpenseCategory(PyEnum):
    """Aina za matumizi ya nyumba"""
    REPAIR    = "repair"      # Ukarabati
    UTILITY   = "utility"     # Maji, umeme, internet
    CLEANING  = "cleaning"    # Usafi
    SECURITY  = "security"    # Ulinzi
    OTHER     = "other"       # Nyingine


# =============================================================================
# MODEL 1: Building (Jengo)
# =============================================================================

class Building(db.Model):
    """
    Inawakilisha jengo moja — nyumba kubwa au nyumba ndogo.
    Kwenye mradi wetu Morogoro tuna majengo MAWILI:
      - Nyumba Kubwa (mbele) — vyumba 4
      - Nyumba Ndogo (nyuma) — vyumba 3
    """
    __tablename__ = "buildings"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    # mfano: "Nyumba Kubwa (Mbele)" au "Nyumba Ndogo (Nyuma)"

    description = db.Column(db.Text, nullable=True)
    address     = db.Column(db.String(200), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Uhusiano (Relationships)
    # building moja ina vyumba vingi → one-to-many
    rooms    = db.relationship("Room",    back_populates="building",
                                cascade="all, delete-orphan", lazy="select")
    # building moja ina matumizi mengi → one-to-many
    expenses = db.relationship("Expense", back_populates="building",
                                cascade="all, delete-orphan", lazy="select")

    # ── Methods ──────────────────────────────────────────────────────────

    def total_rooms(self):
        """Hesabu idadi ya vyumba vyote"""
        return len(self.rooms)

    def occupied_rooms(self):
        """Hesabu vyumba vilivyopangishwa"""
        return sum(1 for r in self.rooms if r.is_occupied)

    def vacant_rooms(self):
        """Vyumba visiyo na mpangaji"""
        return [r for r in self.rooms if not r.is_occupied]

    def monthly_income_potential(self):
        """Kodi inayoweza kukusanywa kila mwezi ukiwa kamili"""
        return sum(r.monthly_rent for r in self.rooms)

    def monthly_income_actual(self, month: int, year: int):
        """Kodi iliyolipwa kwa mwezi fulani"""
        total = 0
        for room in self.rooms:
            if room.tenant:
                paid = sum(
                    p.amount for p in room.tenant.payments
                    if p.month == month
                    and p.year  == year
                    and p.status == PaymentStatus.PAID
                )
                total += paid
        return total

    def __repr__(self):
        return f"<Building id={self.id} name='{self.name}'>"

    def to_dict(self):
        return {
            "id":          self.id,
            "name":        self.name,
            "description": self.description,
            "address":     self.address,
            "total_rooms": self.total_rooms(),
            "occupied":    self.occupied_rooms(),
            "vacant":      len(self.vacant_rooms()),
        }


# =============================================================================
# MODEL 2: Room (Chumba)
# =============================================================================

class Room(db.Model):
    """
    Inawakilisha chumba kimoja ndani ya jengo.
    Chumba kinaweza kuwa:
      - Wazi (is_occupied=False)  → hakuna mpangaji
      - Kimepangishwa (is_occupied=True) → kuna mpangaji mmoja

    Kumbuka: Kwenye nyumba ndogo, baadhi ya wapangaji wanashiriki
    bafu/choo/jiko — hii inaonyeshwa na shared_facilities=True.
    """
    __tablename__ = "rooms"

    id            = db.Column(db.Integer, primary_key=True)
    building_id   = db.Column(db.Integer, db.ForeignKey("buildings.id"),
                               nullable=False)
    room_number   = db.Column(db.String(50), nullable=False)
    # mfano: "Chumba 1", "Chumba cha kati", "Chumba 1 & 2"

    description       = db.Column(db.Text, nullable=True)
    monthly_rent      = db.Column(db.Float, nullable=False, default=0.0)
    is_occupied       = db.Column(db.Boolean, default=False)
    shared_facilities = db.Column(db.Boolean, default=False)
    # True = wapangaji wanashiriki choo/bafu/jiko na wengine

    vacant_since  = db.Column(db.Date, nullable=True)
    # Tarehe chumba kilipokuwa wazi — kwa ripoti ya hasara ya kodi

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Uhusiano
    building = db.relationship("Building", back_populates="rooms")
    # chumba kimoja kina mpangaji mmoja tu kwa wakati mmoja → one-to-one
    tenant   = db.relationship("Tenant", back_populates="room",
                                uselist=False)  # uselist=False = one-to-one

    # ── Methods ──────────────────────────────────────────────────────────

    def days_vacant(self):
        """Siku ngapi chumba kimekuwa wazi"""
        if self.is_occupied or not self.vacant_since:
            return 0
        return (date.today() - self.vacant_since).days

    def lost_income(self):
        """Hasara ya kodi kwa sababu ya chumba wazi"""
        if self.is_occupied:
            return 0.0
        months_vacant = self.days_vacant() / 30
        return round(self.monthly_rent * months_vacant, 2)

    def assign_tenant(self, tenant):
        """Panga mpangaji kwenye chumba hiki"""
        self.is_occupied  = True
        self.vacant_since = None
        self.tenant       = tenant

    def remove_tenant(self):
        """Toa mpangaji — chumba kinakuwa wazi"""
        self.is_occupied  = False
        self.vacant_since = date.today()
        self.tenant       = None

    def __repr__(self):
        status = "occupied" if self.is_occupied else "vacant"
        return f"<Room id={self.id} number='{self.room_number}' {status}>"

    def to_dict(self):
        return {
            "id":                self.id,
            "building_id":       self.building_id,
            "room_number":       self.room_number,
            "monthly_rent":      self.monthly_rent,
            "is_occupied":       self.is_occupied,
            "shared_facilities": self.shared_facilities,
            "days_vacant":       self.days_vacant(),
            "lost_income":       self.lost_income(),
            "tenant":            self.tenant.name if self.tenant else None,
        }


# =============================================================================
# MODEL 3: Tenant (Mpangaji)
# =============================================================================

class Tenant(db.Model):
    """
    Inawakilisha mpangaji mmoja.
    Mpangaji ana chumba kimoja (room_id) na malipo mengi (payments).

    Usalama muhimu: Mpangaji HAWEZI kuona taarifa za mpangaji mwingine.
    Hii inatekelezwa kwenye routes (auth.py) — sio hapa.
    """
    __tablename__ = "tenants"

    id         = db.Column(db.Integer, primary_key=True)
    room_id    = db.Column(db.Integer, db.ForeignKey("rooms.id"),
                            nullable=False)

    name       = db.Column(db.String(150), nullable=False)
    phone      = db.Column(db.String(20),  nullable=True)
    # Namba ya simu — kwa WhatsApp/SMS reminder

    id_number  = db.Column(db.String(50),  nullable=True)
    # Namba ya kitambulisho (NIDA, passport, etc.)

    start_date = db.Column(db.Date, default=date.today)
    end_date   = db.Column(db.Date, nullable=True)
    # end_date = None maana bado yuko. Akiondoka tunaweka tarehe.

    is_active  = db.Column(db.Boolean, default=True)
    # False = ameondoka — hatufuti record, tunabadilisha tu hii

    notes      = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"),
                            nullable=True)
    # Ni admin yupi aliyeandikisha mpangaji huyu

    # Uhusiano
    room     = db.relationship("Room",    back_populates="tenant")
    payments = db.relationship("Payment", back_populates="tenant",
                                cascade="all, delete-orphan",
                                order_by="Payment.year.desc(), Payment.month.desc()")

    # ── Methods ──────────────────────────────────────────────────────────

    def total_paid(self):
        """Jumla ya kodi yote iliyolipwa tangu alipoanza"""
        return sum(p.amount for p in self.payments
                   if p.status == PaymentStatus.PAID)

    def total_owed(self):
        """Jumla ya deni lote bado halijalipiwa"""
        return sum(p.amount for p in self.payments
                   if p.status in (PaymentStatus.DUE, PaymentStatus.LATE))

    def payment_for_month(self, month: int, year: int):
        """Pata kumbukumbu ya malipo ya mwezi fulani"""
        for p in self.payments:
            if p.month == month and p.year == year:
                return p
        return None

    def months_tenanted(self):
        """Miezi ngapi amekaa"""
        end = self.end_date or date.today()
        delta = end - self.start_date
        return max(1, delta.days // 30)

    def has_debt(self):
        """Je, ana deni?"""
        return self.total_owed() > 0

    def __repr__(self):
        return f"<Tenant id={self.id} name='{self.name}' active={self.is_active}>"

    def to_dict(self):
        return {
            "id":          self.id,
            "name":        self.name,
            "phone":       self.phone,
            "room":        self.room.room_number if self.room else None,
            "building":    self.room.building.name if self.room else None,
            "start_date":  str(self.start_date),
            "is_active":   self.is_active,
            "total_paid":  self.total_paid(),
            "total_owed":  self.total_owed(),
            "has_debt":    self.has_debt(),
        }


# =============================================================================
# MODEL 4: Payment (Malipo)
# =============================================================================

class Payment(db.Model):
    """
    Kumbukumbu ya malipo ya kodi ya mwezi mmoja kwa mpangaji mmoja.
    Kila mwezi = kumbukumbu moja.

    Mfano:
      Amani Mwamba, Mei 2025, TZS 250,000, status=PAID
      Fatuma Ali,   Mei 2025, TZS 80,000,  status=LATE
    """
    __tablename__ = "payments"

    id          = db.Column(db.Integer, primary_key=True)
    tenant_id   = db.Column(db.Integer, db.ForeignKey("tenants.id"),
                             nullable=False)

    amount       = db.Column(db.Float,   nullable=False)
    month        = db.Column(db.Integer, nullable=False)  # 1–12
    year         = db.Column(db.Integer, nullable=False)  # mfano: 2025
    payment_date = db.Column(db.Date,    nullable=True)
    # Tarehe halisi ilipopokewa pesa — None kama bado hajalipa

    status      = db.Column(db.Enum(PaymentStatus),
                             default=PaymentStatus.DUE,
                             nullable=False)

    notes       = db.Column(db.Text,    nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"),
                             nullable=True)
    # Admin yupi aliyerekodi malipo haya
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    # Uhusiano
    tenant      = db.relationship("Tenant", back_populates="payments")

    # ── Methods ──────────────────────────────────────────────────────────

    def mark_as_paid(self, paid_by_user_id: int = None):
        """Weka malipo kama yamepokewa"""
        self.status       = PaymentStatus.PAID
        self.payment_date = date.today()
        self.recorded_by  = paid_by_user_id
        self.updated_at   = datetime.utcnow()

    def mark_as_late(self):
        """Weka kama deni — mwezi umepita bila kulipa"""
        self.status = PaymentStatus.LATE

    def is_overdue(self):
        """Je, ni deni la zamani?"""
        return self.status == PaymentStatus.LATE

    def month_name(self):
        """Jina la mwezi kwa Kiswahili"""
        months = {
            1:"Januari", 2:"Februari", 3:"Machi", 4:"Aprili",
            5:"Mei", 6:"Juni", 7:"Julai", 8:"Agosti",
            9:"Septemba", 10:"Oktoba", 11:"Novemba", 12:"Desemba"
        }
        return months.get(self.month, str(self.month))

    def __repr__(self):
        return (f"<Payment id={self.id} tenant_id={self.tenant_id} "
                f"{self.month_name()} {self.year} "
                f"TZS {self.amount:,.0f} [{self.status.value}]>")

    def to_dict(self):
        return {
            "id":           self.id,
            "tenant_id":    self.tenant_id,
            "tenant_name":  self.tenant.name if self.tenant else None,
            "amount":       self.amount,
            "month":        self.month,
            "month_name":   self.month_name(),
            "year":         self.year,
            "status":       self.status.value,
            "payment_date": str(self.payment_date) if self.payment_date else None,
        }


# =============================================================================
# MODEL 5: Expense (Matumizi)
# =============================================================================

class Expense(db.Model):
    """
    Matumizi ya nyumba — ukarabati, maji, umeme, n.k.
    Inahusishwa na jengo (Building), sio chumba moja.

    Ripoti ya faida = Kodi iliyokusanywa − Matumizi yote
    """
    __tablename__ = "expenses"

    id          = db.Column(db.Integer, primary_key=True)
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"),
                             nullable=False)

    category    = db.Column(db.Enum(ExpenseCategory),
                             default=ExpenseCategory.OTHER,
                             nullable=False)
    amount      = db.Column(db.Float,   nullable=False)
    description = db.Column(db.Text,    nullable=False)
    expense_date= db.Column(db.Date,    default=date.today)
    month       = db.Column(db.Integer, nullable=False)
    year        = db.Column(db.Integer, nullable=False)

    receipt_ref = db.Column(db.String(100), nullable=True)
    # Namba ya risiti au stakabadhi kama ipo

    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"),
                             nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Uhusiano
    building = db.relationship("Building", back_populates="expenses")

    # ── Methods ──────────────────────────────────────────────────────────

    def category_label(self):
        """Jina la aina ya matumizi kwa Kiswahili"""
        labels = {
            ExpenseCategory.REPAIR:   "Ukarabati",
            ExpenseCategory.UTILITY:  "Huduma (Maji/Umeme)",
            ExpenseCategory.CLEANING: "Usafi",
            ExpenseCategory.SECURITY: "Ulinzi",
            ExpenseCategory.OTHER:    "Nyingine",
        }
        return labels.get(self.category, self.category.value)

    def __repr__(self):
        return (f"<Expense id={self.id} "
                f"category={self.category.value} "
                f"TZS {self.amount:,.0f} "
                f"{self.month}/{self.year}>")

    def to_dict(self):
        return {
            "id":           self.id,
            "building_id":  self.building_id,
            "category":     self.category.value,
            "category_label": self.category_label(),
            "amount":       self.amount,
            "description":  self.description,
            "expense_date": str(self.expense_date),
            "month":        self.month,
            "year":         self.year,
        }


# =============================================================================
# MODEL 6: User (Mtumiaji wa mfumo — Admin au Tenant)
# =============================================================================

class User(db.Model):
    """
    Mtumiaji wa mfumo wa MIV.
    Kuna aina tatu:
      - admin1: Msimamizi mkuu — anaona kila kitu
      - admin2: Msimamizi msaidizi — anaingiza malipo tu
      - tenant: Mpangaji — anaona risiti yake tu

    USALAMA: Nywila haihifadhiwi wazi kamwe.
    Tunatumia bcrypt (itatekelezwa kwenye auth.py).
    """
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # MUHIMU: hii ni hash, sio nywila halisi

    role          = db.Column(db.Enum(UserRole),
                               default=UserRole.ADMIN2,
                               nullable=False)

    full_name     = db.Column(db.String(150), nullable=True)
    phone         = db.Column(db.String(20),  nullable=True)
    is_active     = db.Column(db.Boolean,     default=True)

    tenant_id     = db.Column(db.Integer, db.ForeignKey("tenants.id"),
                               nullable=True)
    # Kama role=TENANT, hii inaonyesha ni mpangaji yupi

    last_login    = db.Column(db.DateTime, nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Methods ──────────────────────────────────────────────────────────

    def is_admin1(self):
        return self.role == UserRole.ADMIN1

    def is_admin2(self):
        return self.role == UserRole.ADMIN2

    def is_tenant_user(self):
        return self.role == UserRole.TENANT

    def can_view_reports(self):
        """Ni admin1 tu anayeweza kuona ripoti"""
        return self.role == UserRole.ADMIN1

    def can_manage_expenses(self):
        """Ni admin1 tu anayeweza kurekodi matumizi"""
        return self.role == UserRole.ADMIN1

    def can_add_tenants(self):
        """Admin1 na Admin2 wanaweza kuongeza wapangaji"""
        return self.role in (UserRole.ADMIN1, UserRole.ADMIN2)

    def can_record_payments(self):
        """Admin1 na Admin2 wanaweza kurekodi malipo"""
        return self.role in (UserRole.ADMIN1, UserRole.ADMIN2)

    def update_last_login(self):
        self.last_login = datetime.utcnow()

    def __repr__(self):
        return f"<User id={self.id} username='{self.username}' role={self.role.value}>"

    def to_dict(self):
        """MUHIMU: password_hash haimo hapa — usalama"""
        return {
            "id":        self.id,
            "username":  self.username,
            "role":      self.role.value,
            "full_name": self.full_name,
            "is_active": self.is_active,
        }
