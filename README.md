# MIV Morogoro 🏠
**Mietimmobilienverwaltung — Usimamizi wa Majengo ya Kupangisha**

Mfumo wa kusimamia nyumba za kupangisha — Morogoro, Tanzania.

---

## Muundo wa Faili (Project Structure)

```
miv_morogoro/
│
├── app.py          ← Mlango mkuu — endesha hii kuanza mfumo
├── database.py     ← Muunganiko wa database + data ya awali
├── models.py       ← Python classes (Building, Room, Tenant, Payment, Expense, User)
├── auth.py         ← Login, nywila, decorators za usalama
├── requirements.txt← Orodha ya packages zinazohitajika
│
├── routes/         ← (Sprint 2) Routes za kila sehemu
│   ├── main.py     ← Dashboard
│   ├── tenants.py  ← Wapangaji
│   ├── payments.py ← Malipo
│   └── reports.py  ← Ripoti (PDF/CSV)
│
└── templates/      ← (Sprint 2) HTML templates
    ├── base.html
    ├── auth/
    │   └── login.html
    ├── dashboard/
    └── errors/
```

---

## Kuanza (Getting Started)

### Hatua 1: Sakinisha packages
```bash
pip install -r requirements.txt
```

### Hatua 2: Endesha mfumo
```bash
python app.py
```

### Hatua 3: Fungua kivinjari
```
http://localhost:5000/login
```

### Akaunti za awali
| Username | Password   | Role   | Upatikanaji |
|----------|------------|--------|-------------|
| admin    | admin123   | Admin1 | Kamili      |
| hassan   | hassan123  | Admin2 | Mdogo       |

> ⚠️ **Badilisha nywila hizi kabla ya kupeleka mtandaoni!**

---

## Models na Uhusiano (ER Diagram — maandishi)

```
Building (Jengo)
  │
  ├──< Room (Chumba)
  │       │
  │       └──< Tenant (Mpangaji)
  │                   │
  │                   └──< Payment (Malipo)
  │
  └──< Expense (Matumizi)

User (Mtumiaji wa mfumo — Admin au Tenant)
```

---

## Maelezo ya Kila Model

### Building
- Inawakilisha jengo (Nyumba Kubwa / Nyumba Ndogo)
- Ina methods: `total_rooms()`, `vacant_rooms()`, `monthly_income_actual()`

### Room
- Chumba kimoja ndani ya jengo
- `is_occupied=True` kama kuna mpangaji
- `shared_facilities=True` kwa nyumba ndogo (wanashiriki bafu/choo/jiko)
- `days_vacant()` na `lost_income()` kwa ripoti

### Tenant
- Mpangaji mmoja — ana chumba kimoja
- `has_debt()` → True kama ana malipo yaliyochelewa
- `total_paid()` / `total_owed()` kwa historia ya malipo

### Payment
- Kumbukumbu ya malipo ya mwezi mmoja
- Status: PAID / DUE / LATE
- `mark_as_paid(user_id)` → weka kama amelipa

### Expense
- Matumizi ya nyumba (ukarabati, maji, umeme, n.k.)
- Inahusishwa na jengo, sio chumba
- Inatumika kwenye ripoti ya faida (mapato − matumizi)

### User
- Admin1: upatikanaji kamili
- Admin2: ongeza wapangaji + rekodi malipo tu
- Tenant: risiti yake tu

---

## Usalama (Security)

| Hatua | Jinsi inavyotekelezwa |
|-------|----------------------|
| Nywila | bcrypt hash (rounds=12) — haihifadhiwi wazi |
| Login | Flask session — inafutwa ukitoka |
| Roles | Decorators: `@admin1_required`, `@admin_required` |
| Tenant data | Kila query inachuja kwa `tenant_id` ya mtumiaji |
| Debug mode | `debug=False` kwenye production |

---

## Agile Sprint Log

### ✅ Sprint 1 (Wiki 1–2) — IMEKAMILIKA
- [x] `models.py` — classes zote 6
- [x] `database.py` — SQLAlchemy setup + seed data
- [x] `auth.py` — bcrypt hashing + login/logout + decorators
- [x] `app.py` — Flask app factory

### 🔄 Sprint 2 (Wiki 3–4) — INAKUJA
- [ ] Dashboard ya Admin1 na Admin2
- [ ] CRUD ya wapangaji
- [ ] Kurekodi malipo
- [ ] Kurekodi matumizi

### 📋 Sprint 3–5 — IMEPANGWA
- Tazama: IHK Documentation → Section 3 (Agile Methodology)

---

## Maswali ya Kujaribu Ujuzi Wako

Baada ya kusoma `models.py`, jaribu kujibu:

1. Kwa nini `User.to_dict()` haina `password_hash`?
2. `uselist=False` kwenye `Room.tenant` inamaanisha nini?
3. Tofauti kati ya `db.session.flush()` na `db.session.commit()` ni nini?
4. Kwa nini tunatumia `Enum` badala ya kuandika "paid"/"due" kama string?
5. `@wraps(f)` kwenye decorator inafanya nini?

*(Majibu yatakuja kwenye Sprint 2 wiki ijayo!)*
