#!/bin/bash
# Start both FastAPI backend and React frontend
echo "Starting Pathfinder..."

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Load .env into the shell so uvicorn inherits the credentials directly
cd "$(dirname "$0")"
set -a
source .env
set +a

python3 -m uvicorn api.main:app --reload --port 8001 &
API_PID=$!
echo "✅ FastAPI running at http://localhost:8001  (PID $API_PID)"

# Start React dev server on port 5173
cd react
npm run dev &
REACT_PID=$!
echo "✅ React running at http://localhost:5173  (PID $REACT_PID)"

echo ""
echo "Open: http://localhost:5173"
echo "Press Ctrl+C to stop both servers."

trap "kill $API_PID $REACT_PID 2>/dev/null; exit 0" INT TERM
wait
