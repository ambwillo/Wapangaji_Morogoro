#!/bin/bash
# ============================================
# WAPANGAJI MOROGORO - ANZISHA MFUMO
# ============================================

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║   🏠 WAPANGAJI MOROGORO          ║"
echo "  ║   Mfumo wa Usimamizi wa Nyumba   ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# Angalia Python
if ! command -v python3 &> /dev/null; then
    echo "  KOSA: Python3 haipo. Tafadhali sakinisha Python 3."
    exit 1
fi

# Sakinisha mahitaji kama hayapo
echo "  📦 Kuangalia mahitaji..."
pip3 install fastapi uvicorn python-multipart --break-system-packages -q 2>/dev/null
echo "  ✅ Mahitaji yako sawa"

# Anza backend
echo ""
echo "  🚀 Kuanza Backend (API)..."
cd "$(dirname "$0")/backend"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  ✅ Backend inaendesha: http://localhost:8000"

# Subiri sekunde 2 backend ianze
sleep 2

# Anza frontend
echo ""
echo "  🌐 Kuanza Frontend (Dashboard)..."
cd "$(dirname "$0")/frontend"
python3 -m http.server 3000 &
FRONTEND_PID=$!
echo "  ✅ Frontend inaendesha: http://localhost:3000"

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║  🎉 MFUMO UNAENDESHA!               ║"
echo "  ╠══════════════════════════════════════╣"
echo "  ║  Dashboard : http://localhost:3000   ║"
echo "  ║  API Docs  : http://localhost:8000/docs ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
echo "  Bonyeza Ctrl+C kusimamisha mfumo"
echo ""

# Subiri hadi Ctrl+C
trap "echo ''; echo '  Mfumo umesimamishwa.'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
