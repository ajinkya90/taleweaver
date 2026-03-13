#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
#  Taleweaver — Interactive Setup Script
# ─────────────────────────────────────────────────────────────

BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$ROOT_DIR/backend/.env"

echo ""
echo -e "${CYAN}${BOLD}  ╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}  ║        Taleweaver Setup              ║${NC}"
echo -e "${CYAN}${BOLD}  ║   Audio Stories for Kids              ║${NC}"
echo -e "${CYAN}${BOLD}  ╚══════════════════════════════════════╝${NC}"
echo ""

# ── Helper functions ────────────────────────────────────────

prompt_value() {
    local prompt_text="$1"
    local default_value="${2:-}"
    local result

    if [ -n "$default_value" ]; then
        echo -ne "${BOLD}$prompt_text${NC} ${DIM}[$default_value]${NC}: "
        read -r result
        echo "${result:-$default_value}"
    else
        echo -ne "${BOLD}$prompt_text${NC}: "
        read -r result
        echo "$result"
    fi
}

prompt_secret() {
    local prompt_text="$1"
    local result
    echo -ne "${BOLD}$prompt_text${NC}: "
    read -rs result
    echo ""
    echo "$result"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed.${NC}"
        echo -e "${DIM}$2${NC}"
        return 1
    fi
    echo -e "  ${GREEN}✓${NC} $1 found"
    return 0
}

# ── Step 1: Check prerequisites ────────────────────────────

echo -e "${BOLD}Step 1: Checking prerequisites${NC}"
echo ""

MISSING=0
check_command "python3" "Install Python 3.9+: https://python.org" || MISSING=1
check_command "node" "Install Node.js 18+: https://nodejs.org" || MISSING=1
check_command "npm" "Comes with Node.js" || MISSING=1
check_command "ffmpeg" "Install ffmpeg: brew install ffmpeg (macOS) / sudo apt install ffmpeg (Linux)" || MISSING=1

echo ""
if [ "$MISSING" -eq 1 ]; then
    echo -e "${RED}Please install the missing dependencies above and re-run this script.${NC}"
    exit 1
fi
echo -e "${GREEN}All prerequisites found.${NC}"
echo ""

# ── Step 2: Choose LLM Provider ───────────────────────────

echo -e "${BOLD}Step 2: Choose your LLM provider${NC}"
echo ""
echo -e "  Taleweaver supports three LLM providers for story generation:"
echo ""
echo -e "  ${CYAN}1)${NC} ${BOLD}Groq${NC}        — Llama 3.3 70B ${DIM}(free tier available, fast)${NC}"
echo -e "  ${CYAN}2)${NC} ${BOLD}OpenAI${NC}      — GPT-4o ${DIM}(paid, high quality)${NC}"
echo -e "  ${CYAN}3)${NC} ${BOLD}Anthropic${NC}   — Claude Sonnet 4.5 ${DIM}(paid, high quality)${NC}"
echo ""

while true; do
    PROVIDER_NUM=$(prompt_value "Select provider (1/2/3)" "1")
    case "$PROVIDER_NUM" in
        1) LLM_PROVIDER="groq"; break ;;
        2) LLM_PROVIDER="openai"; break ;;
        3) LLM_PROVIDER="anthropic"; break ;;
        *) echo -e "${RED}Invalid choice. Enter 1, 2, or 3.${NC}" ;;
    esac
done

echo ""
echo -e "  Selected: ${GREEN}${BOLD}$LLM_PROVIDER${NC}"
echo ""

# ── Step 3: API Keys ──────────────────────────────────────

echo -e "${BOLD}Step 3: Enter your API keys${NC}"
echo ""

GROQ_API_KEY=""
OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""

case "$LLM_PROVIDER" in
    groq)
        echo -e "  ${DIM}Get your key at: https://console.groq.com/keys${NC}"
        GROQ_API_KEY=$(prompt_secret "  Groq API key")
        if [ -z "$GROQ_API_KEY" ]; then
            echo -e "${RED}  API key is required.${NC}"; exit 1
        fi
        ;;
    openai)
        echo -e "  ${DIM}Get your key at: https://platform.openai.com/api-keys${NC}"
        OPENAI_API_KEY=$(prompt_secret "  OpenAI API key")
        if [ -z "$OPENAI_API_KEY" ]; then
            echo -e "${RED}  API key is required.${NC}"; exit 1
        fi
        ;;
    anthropic)
        echo -e "  ${DIM}Get your key at: https://console.anthropic.com/settings/keys${NC}"
        ANTHROPIC_API_KEY=$(prompt_secret "  Anthropic API key")
        if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo -e "${RED}  API key is required.${NC}"; exit 1
        fi
        ;;
esac

echo ""
echo -e "  ${DIM}ElevenLabs is required for text-to-speech (voice generation).${NC}"
echo -e "  ${DIM}Get your key at: https://elevenlabs.io/app/settings/api-keys${NC}"
echo -e "  ${DIM}Free tier: ~10 minutes of audio per month.${NC}"
ELEVENLABS_API_KEY=$(prompt_secret "  ElevenLabs API key")
if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo -e "${RED}  ElevenLabs API key is required for voice generation.${NC}"; exit 1
fi

echo ""
echo -e "  ${GREEN}✓${NC} API keys collected"
echo ""

# ── Step 4: Write .env file ──────────────────────────────

echo -e "${BOLD}Step 4: Writing configuration${NC}"
echo ""

cat > "$ENV_FILE" <<EOF
LLM_PROVIDER=$LLM_PROVIDER
GROQ_API_KEY=$GROQ_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY

# ElevenLabs Voice IDs (defaults work out of the box — change if you want different voices)
# To find voice IDs: go to https://elevenlabs.io/app/voice-lab, click a voice, copy the Voice ID
NARRATOR_VOICE_ID=21m00Tcm4TlvDq8ikWAM
CHARACTER_MALE_VOICE_ID=ErXwobaYiN019PkySvjV
CHARACTER_FEMALE_VOICE_ID=EXAVITQu4vr4xnSDxMaL
CHARACTER_CHILD_VOICE_ID=jBpfuIE2acCO8z3wKNLl
EOF

echo -e "  ${GREEN}✓${NC} Created $ENV_FILE"
echo ""

# ── Step 5: Install backend dependencies ─────────────────

echo -e "${BOLD}Step 5: Installing backend dependencies${NC}"
echo ""

cd "$ROOT_DIR/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "  ${GREEN}✓${NC} Created Python virtual environment"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo -e "  ${GREEN}✓${NC} Installed Python packages"
echo ""

# ── Step 6: Install frontend dependencies ────────────────

echo -e "${BOLD}Step 6: Installing frontend dependencies${NC}"
echo ""

cd "$ROOT_DIR/frontend"
npm install --silent 2>/dev/null
echo -e "  ${GREEN}✓${NC} Installed Node packages"
echo ""

# ── Step 7: Decide access mode ───────────────────────────

echo -e "${BOLD}Step 7: How do you want to access Taleweaver?${NC}"
echo ""
echo -e "  ${CYAN}1)${NC} ${BOLD}This computer only${NC}   — http://localhost:5173"
echo -e "  ${CYAN}2)${NC} ${BOLD}Local WiFi${NC}           — accessible from phones/tablets on same network"
echo ""

ACCESS_MODE=$(prompt_value "Select (1/2)" "1")

LOCAL_IP=""
if [ "$ACCESS_MODE" = "2" ]; then
    # Detect local IP
    if command -v ipconfig &> /dev/null 2>&1; then
        LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")
    fi
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "")
    fi
    if [ -z "$LOCAL_IP" ]; then
        echo -e "  ${YELLOW}Could not auto-detect your local IP.${NC}"
        LOCAL_IP=$(prompt_value "  Enter your local IP address" "192.168.1.100")
    else
        echo -e "  ${DIM}Detected local IP: $LOCAL_IP${NC}"
    fi
fi

echo ""

# ── Step 8: Create start script ──────────────────────────

echo -e "${BOLD}Step 8: Creating start script${NC}"
echo ""

if [ "$ACCESS_MODE" = "2" ]; then
    BACKEND_HOST="0.0.0.0"
    FRONTEND_HOST="0.0.0.0"
    ACCESS_URL="http://$LOCAL_IP:5173"
else
    BACKEND_HOST="127.0.0.1"
    FRONTEND_HOST="localhost"
    ACCESS_URL="http://localhost:5173"
fi

cat > "$ROOT_DIR/start.sh" <<STARTEOF
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"

echo ""
echo -e "\033[1m\033[36m  Starting Taleweaver...\033[0m"
echo ""

# Start backend
cd "\$ROOT_DIR/backend"
source venv/bin/activate
uvicorn app.main:app --host $BACKEND_HOST --port 8000 &
BACKEND_PID=\$!
echo "  Backend started (PID \$BACKEND_PID)"

# Start frontend
cd "\$ROOT_DIR/frontend"
npx vite --host $FRONTEND_HOST --port 5173 &
FRONTEND_PID=\$!
echo "  Frontend started (PID \$FRONTEND_PID)"

echo ""
echo -e "\033[1m\033[32m  Taleweaver is ready!\033[0m"
echo ""
echo -e "  Open: \033[4m$ACCESS_URL\033[0m"
STARTEOF

if [ "$ACCESS_MODE" = "2" ]; then
    cat >> "$ROOT_DIR/start.sh" <<LANEOF
echo -e "  LAN:  \033[4mhttp://$LOCAL_IP:5173\033[0m"
LANEOF
fi

cat >> "$ROOT_DIR/start.sh" <<'TRAPEOF'
echo ""
echo "  Press Ctrl+C to stop."
echo ""

cleanup() {
    echo ""
    echo "  Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "  Stopped."
}
trap cleanup INT TERM

wait
TRAPEOF

chmod +x "$ROOT_DIR/start.sh"
echo -e "  ${GREEN}✓${NC} Created start.sh"
echo ""

# ── Done ─────────────────────────────────────────────────

echo -e "${GREEN}${BOLD}  ╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}  ║         Setup Complete!              ║${NC}"
echo -e "${GREEN}${BOLD}  ╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "  To start Taleweaver, run:"
echo ""
echo -e "    ${CYAN}./start.sh${NC}"
echo ""
echo -e "  Then open: ${BOLD}$ACCESS_URL${NC}"
echo ""
if [ "$ACCESS_MODE" = "2" ]; then
    echo -e "  Other devices on WiFi can access: ${BOLD}http://$LOCAL_IP:5173${NC}"
    echo ""
fi
echo -e "  ${DIM}Provider: $LLM_PROVIDER | TTS: ElevenLabs${NC}"
echo -e "  ${DIM}Config: backend/.env | Logs: backend/app/logs/${NC}"
echo ""
