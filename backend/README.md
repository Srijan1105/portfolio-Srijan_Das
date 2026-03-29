# Backend Setup

## 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

## 2. Set environment variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

You need a **Gmail App Password** (not your regular password):
- Go to Google Account → Security → 2-Step Verification → App Passwords
- Generate one for "Mail"

## 3. Run the server
```bash
cd backend
python app.py
```

## 4. Update frontend
In `main.js`, set `BACKEND` to your server URL when deploying:
```js
const BACKEND = 'https://your-deployed-url.com';
```
