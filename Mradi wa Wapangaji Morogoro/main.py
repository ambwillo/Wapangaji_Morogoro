from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
from datetime import datetime

app = FastAPI(title="Wapangaji - Morogoro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "/home/claude/wapangaji/backend/wapangaji.db"

VYUMBA = {
    "1": {"jengo": "Mbele",  "aina": "Vyumba Viwili na Sebule", "kodi": 200000},
    "2": {"jengo": "Nyuma",  "aina": "Vyumba Viwili",           "kodi": 100000},
    "3": {"jengo": "Nyuma",  "aina": "Chumba Kimoja",           "kodi":  50000},
    "4": {"jengo": "Nyuma",  "aina": "Chumba Kimoja",           "kodi":  40000},
}

# ── helpers ────────────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hali_malipo(mpangaji_id: int, kodi_kwa_mwezi: int, tarehe_kuingia: str) -> dict:
    """Hesabu deni au ziada kwa mpangaji."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(kiasi_kilicholipwa),0) FROM malipo WHERE mpangaji_id=?", (mpangaji_id,))
    jumla_iliyolipwa = c.fetchone()[0]
    conn.close()

    leo = datetime.now()
    ki  = datetime.strptime(tarehe_kuingia, "%Y-%m-%d")
    miezi = (leo.year - ki.year) * 12 + (leo.month - ki.month) + 1
    inayotarajiwa = miezi * kodi_kwa_mwezi
    deni = inayotarajiwa - jumla_iliyolipwa
    return {
        "miezi": miezi,
        "jumla_inayotarajiwa": inayotarajiwa,
        "jumla_iliyolipwa": jumla_iliyolipwa,
        "deni": deni,
    }

def row_mpangaji(row) -> dict:
    d = dict(row)
    fin = hali_malipo(d["id"], d["kiasi_cha_kodi"], d["tarehe_ya_kuingia"])
    d.update(fin)
    return d

# ── database init ──────────────────────────────────────────────────────────────

def anzisha_database():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS wapangaji (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jina_kamili TEXT NOT NULL,
            namba_ya_simu TEXT,
            namba_ya_chumba TEXT,
            jengo TEXT,
            aina_ya_chumba TEXT,
            kiasi_cha_kodi INTEGER,
            tarehe_ya_kuingia TEXT,
            tarehe_ya_kuondoka TEXT,
            hali TEXT DEFAULT 'Anaishi'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS malipo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mpangaji_id INTEGER,
            kiasi_kilicholipwa INTEGER,
            tarehe_ya_kulipa TEXT,
            mwezi_unaolipwa TEXT,
            njia_ya_kulipa TEXT,
            maelezo TEXT,
            FOREIGN KEY (mpangaji_id) REFERENCES wapangaji(id)
        )
    ''')
    conn.commit()
    conn.close()

anzisha_database()

# ── Pydantic models ────────────────────────────────────────────────────────────

class MpangaziIngiza(BaseModel):
    jina_kamili: str
    namba_ya_simu: Optional[str] = None
    namba_ya_chumba: str
    tarehe_ya_kuingia: str          # YYYY-MM-DD

class MalipoIngiza(BaseModel):
    mpangaji_id: int
    kiasi_kilicholipwa: int
    mwezi_unaolipwa: str
    njia_ya_kulipa: str
    maelezo: Optional[str] = ""

class KuondokaIngiza(BaseModel):
    tarehe_ya_kuondoka: str         # YYYY-MM-DD

# ── ROUTES ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"ujumbe": "Wapangaji Morogoro API iko hai!"}

# --- vyumba ---
@app.get("/vyumba")
def pata_vyumba():
    conn = get_conn()
    c = conn.cursor()
    result = []
    for namba, info in VYUMBA.items():
        c.execute("SELECT jina_kamili FROM wapangaji WHERE namba_ya_chumba=? AND hali='Anaishi'", (namba,))
        mkazi = c.fetchone()
        result.append({
            "namba": namba,
            **info,
            "imechukuliwa": bool(mkazi),
            "mkazi_sasa": mkazi["jina_kamili"] if mkazi else None,
        })
    conn.close()
    return result

# --- wapangaji ---
@app.get("/wapangaji")
def pata_wapangaji(hali: Optional[str] = None):
    conn = get_conn()
    c = conn.cursor()
    if hali:
        c.execute("SELECT * FROM wapangaji WHERE hali=? ORDER BY namba_ya_chumba", (hali,))
    else:
        c.execute("SELECT * FROM wapangaji ORDER BY namba_ya_chumba")
    wote = [row_mpangaji(r) for r in c.fetchall()]
    conn.close()
    return wote

@app.get("/wapangaji/{mpangaji_id}")
def pata_mpangaji(mpangaji_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM wapangaji WHERE id=?", (mpangaji_id,))
    m = c.fetchone()
    if not m:
        raise HTTPException(404, "Mpangaji hapatikani")
    data = row_mpangaji(m)
    c.execute("""
        SELECT * FROM malipo WHERE mpangaji_id=? ORDER BY tarehe_ya_kulipa ASC
    """, (mpangaji_id,))
    data["malipo"] = [dict(r) for r in c.fetchall()]
    conn.close()
    return data

@app.post("/wapangaji", status_code=201)
def ongeza_mpangaji(data: MpangaziIngiza):
    if data.namba_ya_chumba not in VYUMBA:
        raise HTTPException(400, "Namba ya chumba si sahihi (1-4)")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM wapangaji WHERE namba_ya_chumba=? AND hali='Anaishi'", (data.namba_ya_chumba,))
    if c.fetchone():
        conn.close()
        raise HTTPException(409, f"Chumba {data.namba_ya_chumba} kimeshachukuliwa")
    info = VYUMBA[data.namba_ya_chumba]
    c.execute('''
        INSERT INTO wapangaji
        (jina_kamili, namba_ya_simu, namba_ya_chumba, jengo, aina_ya_chumba,
         kiasi_cha_kodi, tarehe_ya_kuingia, hali)
        VALUES (?,?,?,?,?,?,?,'Anaishi')
    ''', (data.jina_kamili, data.namba_ya_simu, data.namba_ya_chumba,
          info["jengo"], info["aina"], info["kodi"], data.tarehe_ya_kuingia))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"ujumbe": "Mpangaji amesajiliwa", "id": new_id}

@app.put("/wapangaji/{mpangaji_id}/ondoka")
def toa_mpangaji(mpangaji_id: int, data: KuondokaIngiza):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM wapangaji WHERE id=?", (mpangaji_id,))
    m = c.fetchone()
    if not m:
        conn.close()
        raise HTTPException(404, "Mpangaji hapatikani")
    fin = hali_malipo(mpangaji_id, m["kiasi_cha_kodi"], m["tarehe_ya_kuingia"])
    c.execute("""
        UPDATE wapangaji SET hali='Ameondoka', tarehe_ya_kuondoka=? WHERE id=?
    """, (data.tarehe_ya_kuondoka, mpangaji_id))
    conn.commit()
    conn.close()
    return {"ujumbe": "Mpangaji amesajiliwa kuondoka", "deni_lililobaki": fin["deni"]}

# --- malipo ---
@app.get("/malipo/{mpangaji_id}")
def pata_malipo(mpangaji_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM malipo WHERE mpangaji_id=? ORDER BY tarehe_ya_kulipa DESC", (mpangaji_id,))
    malipo = [dict(r) for r in c.fetchall()]
    conn.close()
    return malipo

@app.post("/malipo", status_code=201)
def ingiza_malipo(data: MalipoIngiza):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM wapangaji WHERE id=?", (data.mpangaji_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(404, "Mpangaji hapatikani")
    tarehe_leo = datetime.now().strftime("%Y-%m-%d")
    c.execute('''
        INSERT INTO malipo
        (mpangaji_id, kiasi_kilicholipwa, tarehe_ya_kulipa, mwezi_unaolipwa, njia_ya_kulipa, maelezo)
        VALUES (?,?,?,?,?,?)
    ''', (data.mpangaji_id, data.kiasi_kilicholipwa, tarehe_leo,
          data.mwezi_unaolipwa, data.njia_ya_kulipa, data.maelezo))
    conn.commit()
    conn.close()
    return {"ujumbe": "Malipo yamehifadhiwa"}

# --- madeni / dashboard stats ---
@app.get("/madeni")
def pata_madeni():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM wapangaji WHERE hali='Anaishi'")
    wote = c.fetchall()
    conn.close()
    wadaiwa = []
    for m in wote:
        fin = hali_malipo(m["id"], m["kiasi_cha_kodi"], m["tarehe_ya_kuingia"])
        if fin["deni"] > 0:
            wadaiwa.append({**dict(m), **fin})
    jumla_deni = sum(w["deni"] for w in wadaiwa)
    return {"wadaiwa": wadaiwa, "jumla_deni": jumla_deni, "idadi": len(wadaiwa)}

@app.get("/dashibodi")
def pata_dashibodi():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM wapangaji WHERE hali='Anaishi'")
    wanaishi = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM wapangaji WHERE hali='Ameondoka'")
    wameondoka = c.fetchone()["n"]
    vyumba_huru = sum(
        1 for namba in VYUMBA
        if not (c.execute("SELECT 1 FROM wapangaji WHERE namba_ya_chumba=? AND hali='Anaishi'", (namba,)).fetchone())
    )
    c.execute("SELECT COALESCE(SUM(kiasi_kilicholipwa),0) as s FROM malipo m JOIN wapangaji w ON m.mpangaji_id=w.id WHERE w.hali='Anaishi'")
    jumla_iliyolipwa = c.fetchone()["s"]
    conn.close()

    # jumla inayotarajiwa
    conn2 = get_conn()
    c2 = conn2.cursor()
    c2.execute("SELECT * FROM wapangaji WHERE hali='Anaishi'")
    wote = c2.fetchall()
    conn2.close()
    jumla_inayotarajiwa = 0
    jumla_deni = 0
    for m in wote:
        fin = hali_malipo(m["id"], m["kiasi_cha_kodi"], m["tarehe_ya_kuingia"])
        jumla_inayotarajiwa += fin["jumla_inayotarajiwa"]
        if fin["deni"] > 0:
            jumla_deni += fin["deni"]

    return {
        "wapangaji_wanaishi": wanaishi,
        "wapangaji_wameondoka": wameondoka,
        "vyumba_huru": vyumba_huru,
        "vyumba_vyote": len(VYUMBA),
        "jumla_iliyolipwa": jumla_iliyolipwa,
        "jumla_inayotarajiwa": jumla_inayotarajiwa,
        "jumla_deni": jumla_deni,
    }

# --- SMS reminder text generator ---
@app.get("/sms/{mpangaji_id}")
def tengeneza_sms(mpangaji_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM wapangaji WHERE id=?", (mpangaji_id,))
    m = c.fetchone()
    conn.close()
    if not m:
        raise HTTPException(404, "Mpangaji hapatikani")
    fin = hali_malipo(mpangaji_id, m["kiasi_cha_kodi"], m["tarehe_ya_kuingia"])
    deni = fin["deni"]
    if deni <= 0:
        sms = (f"Ndugu {m['jina_kamili']}, malipo yako ya kodi yako sawa. "
               f"Asante kwa ushirikiano. - Menejimenti")
    else:
        sms = (f"Ndugu {m['jina_kamili']}, deni lako la kodi hadi sasa ni "
               f"TZS {deni:,}. Tafadhali lipa haraka. "
               f"Kodi ya mwezi: TZS {m['kiasi_cha_kodi']:,}. - Menejimenti")
    return {"simu": m["namba_ya_simu"], "ujumbe": sms, "deni": deni}
