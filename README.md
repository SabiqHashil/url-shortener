# MiniCut – URL Shortener

## Run locally
python -m venv .venv && . .venv/bin/activate  
pip install -r requirements.txt  
FLASK_DEBUG=1 python app.py  
Open http://127.0.0.1:5000

## Docker (one command)
docker compose up --build  
Open http://127.0.0.1:8000

## API
POST /api/shorten
{
  "url": "https://example.com",
  "code": "optional",
  "expiry_hours": 24
}
