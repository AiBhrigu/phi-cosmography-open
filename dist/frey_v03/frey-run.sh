set -e

echo "▶ Installing FREY v0.3"
pip install -e .

echo "▶ Launching API"
uvicorn frey_api.main:app --port 8811 --reload &
PID=$!

sleep 3

echo "▶ Smoke-test"
curl http://127.0.0.1:8811/ping
curl -X POST http://127.0.0.1:8811/phi-passport -H "Content-Type: application/json" -d '{"user_id":"test","birth_date":19910412}'

kill $PID
echo "DONE"
