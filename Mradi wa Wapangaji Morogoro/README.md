# 🏠 Wapangaji Morogoro — Mfumo wa Usimamizi wa Nyumba

## Muundo wa Mfumo

```
wapangaji/
├── backend/
│   ├── main.py          ← API (FastAPI + SQLite)
│   └── wapangaji.db     ← Database (inatengenezwa otomatiki)
├── frontend/
│   └── index.html       ← Dashboard (React)
├── anzisha.sh           ← Script ya kuanzisha mfumo
└── README.md
```

---

## 🚀 Jinsi ya Kuanzisha

### Hatua 1 — Sakinisha Python (mara moja tu)
```bash
# Ubuntu/Debian/Raspberry Pi:
sudo apt install python3 python3-pip

# macOS:
brew install python3
```

### Hatua 2 — Anza Mfumo
```bash
cd wapangaji
chmod +x anzisha.sh
./anzisha.sh
```

### Hatua 3 — Fungua Browser
- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

---

## 📱 API Endpoints

| Method | URL | Maelezo |
|--------|-----|---------|
| GET | `/dashibodi` | Takwimu za jumla |
| GET | `/vyumba` | Hali ya vyumba vyote |
| GET | `/wapangaji` | Orodha ya wapangaji |
| GET | `/wapangaji/{id}` | Taarifa kamili + malipo |
| POST | `/wapangaji` | Ongeza mpangaji mpya |
| PUT | `/wapangaji/{id}/ondoka` | Saidia mpangaji kuondoka |
| POST | `/malipo` | Ingiza malipo |
| GET | `/madeni` | Wanaodaiwa kodi |
| GET | `/sms/{id}` | Tengeneza SMS ya ukumbusho |

---

## 🟢 Hatua Inayofuata — WhatsApp Bot

Admin ataweza kutuma WhatsApp kama:
- `"lipa 101 50000 Mei 2025"` → Ingiza malipo kwa ID 101
- `"deni 102"` → Angalia deni la mpangaji 102
- `"orodha"` → Orodha ya wapangaji wote
- `"madeni"` → Wote wanaodaiwa

Tutatumia: **Twilio WhatsApp API** (free trial inapatikana)

---

## 🐛 Tatizo?

**API haikuanza:**
```bash
pip3 install fastapi uvicorn --break-system-packages
```

**Port imeshachukuliwa:**
```bash
# Badilisha port kwenye anzisha.sh (8000→8001, 3000→3001)
```
