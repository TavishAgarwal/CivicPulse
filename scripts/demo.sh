#!/bin/bash
# ============================================================
# CivicPulse — One-Command Demo Script
# Usage: bash scripts/demo.sh
#        bash scripts/demo.sh --demo-only
# ============================================================
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

DEMO_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --demo-only) DEMO_ONLY=true ;;
  esac
done

# ── Banner ──────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}"
echo "   ╔══════════════════════════════════════════════╗"
echo "   ║                                              ║"
echo "   ║    ◉  C I V I C P U L S E                    ║"
echo "   ║    Hyperlocal Need Prediction Platform       ║"
echo "   ║                                              ║"
echo "   ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: Environment Setup ──────────────────────────────
echo -e "${YELLOW}▸ Step 1: Checking environment...${NC}"

if [ ! -f "$PROJECT_DIR/.env" ]; then
  if [ -f "$PROJECT_DIR/.env.example" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "  ${GREEN}✓${NC} Created .env from .env.example"
  else
    echo -e "  ${YELLOW}⚠${NC} No .env.example found — continuing with defaults"
  fi
else
  echo -e "  ${GREEN}✓${NC} .env already exists"
fi

# ── Step 2: Generate Synthetic Data ────────────────────────
echo -e "${YELLOW}▸ Step 2: Generating synthetic data...${NC}"

if command -v python3 &>/dev/null; then
  PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
  PYTHON_CMD="python"
else
  PYTHON_CMD=""
fi

if [ -n "$PYTHON_CMD" ]; then
  if [ ! -f "$PROJECT_DIR/data/synthetic/signals_sample.json" ]; then
    cd "$PROJECT_DIR"
    $PYTHON_CMD data/synthetic/generate.py --city delhi --wards 50 --days 60 --seed 42
    echo -e "  ${GREEN}✓${NC} Synthetic data generated"
  else
    echo -e "  ${GREEN}✓${NC} Synthetic data already exists"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} Python not found — skipping data generation (dashboard uses built-in demo data)"
fi

# ── Step 3: Launch Services ────────────────────────────────
echo -e "${YELLOW}▸ Step 3: Launching services...${NC}"

# Function to open browser cross-platform
open_browser() {
  local url="$1"
  if command -v open &>/dev/null; then
    open "$url"              # macOS
  elif command -v xdg-open &>/dev/null; then
    xdg-open "$url"          # Linux
  elif command -v start &>/dev/null; then
    start "$url"             # Windows (Git Bash)
  else
    echo -e "  ${YELLOW}⚠${NC} Could not auto-open browser. Navigate to: $url"
  fi
}

if [ "$DEMO_ONLY" = true ]; then
  echo -e "  ${CYAN}ℹ${NC} --demo-only mode: launching frontend only"

  # Check for Node.js
  if ! command -v npm &>/dev/null; then
    echo -e "  ${RED}✗${NC} npm not found. Install Node.js v18+ to run the dashboard."
    exit 1
  fi

  cd "$PROJECT_DIR/src/dashboard"

  # Install deps if needed
  if [ ! -d "node_modules" ]; then
    echo -e "  ${CYAN}ℹ${NC} Installing dependencies..."
    npm install --silent
  fi

  echo -e "  ${GREEN}✓${NC} Starting dashboard (demo mode — mock data)..."
  echo ""

  # Start dev server in background
  npm run dev -- --host 0.0.0.0 --port 3000 &
  DEV_PID=$!

  # Wait for server
  echo -e "  ${CYAN}ℹ${NC} Waiting for dashboard at http://localhost:3000..."
  for i in $(seq 1 30); do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  sleep 2
  open_browser "http://localhost:3000"

  echo ""
  echo -e "${GREEN}${BOLD}"
  echo "  ╔══════════════════════════════════════════════╗"
  echo "  ║                                              ║"
  echo "  ║  🌟 CivicPulse is running!                  ║"
  echo "  ║                                              ║"
  echo "  ║  📊 Dashboard: http://localhost:3000         ║"
  echo "  ║  👤 Demo login:                              ║"
  echo "  ║     coordinator@civicpulse.demo / demo123    ║"
  echo "  ║                                              ║"
  echo "  ║  Mode: DEMO ONLY (mock data)                 ║"
  echo "  ║  Press Ctrl+C to stop                        ║"
  echo "  ║                                              ║"
  echo "  ╚══════════════════════════════════════════════╝"
  echo -e "${NC}"

  # Wait for dev server
  wait $DEV_PID

else
  # Full Docker mode
  DOCKER_AVAILABLE=false

  if command -v docker &>/dev/null && docker info >/dev/null 2>&1; then
    DOCKER_AVAILABLE=true
  fi

  if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "  ${GREEN}✓${NC} Docker is running"

    cd "$PROJECT_DIR"

    # Use lite compose if available, otherwise full
    if [ -f "docker-compose.lite.yml" ]; then
      echo -e "  ${CYAN}ℹ${NC} Using lightweight stack (no Kafka)"
      docker-compose -f docker-compose.lite.yml up -d --build
    else
      echo -e "  ${CYAN}ℹ${NC} Using full stack"
      docker-compose up -d --build
    fi

    echo -e "  ${CYAN}ℹ${NC} Waiting for services to start..."
    for i in $(seq 1 60); do
      if curl -s http://localhost:3000 >/dev/null 2>&1; then
        break
      fi
      sleep 2
    done

    sleep 3
    open_browser "http://localhost:3000"

    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════╗"
    echo "  ║                                              ║"
    echo "  ║  🌟 CivicPulse is running!                  ║"
    echo "  ║                                              ║"
    echo "  ║  📊 Dashboard:  http://localhost:3000        ║"
    echo "  ║  📡 API docs:   http://localhost:8000/docs   ║"
    echo "  ║  👤 Demo login:                              ║"
    echo "  ║     coordinator@civicpulse.demo / demo123    ║"
    echo "  ║                                              ║"
    echo "  ║  Stop: docker-compose down                   ║"
    echo "  ║                                              ║"
    echo "  ╚══════════════════════════════════════════════╝"
    echo -e "${NC}"

  else
    echo -e "  ${YELLOW}⚠${NC} Docker not running — falling back to demo-only mode"
    exec "$0" --demo-only
  fi
fi
