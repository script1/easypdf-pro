# EasyPDF Deployment Guide

## 1. Backend (Python/FastAPI) - Deploy to Render.com
1. Create a new **Web Service** on Render.
2. Connect your repository.
3. Use the following settings:
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT` (or it will auto-detect from Procfile)
4. **Environment Variables**:
    - `ALLOWED_ORIGINS`: Add the URL of your Vercel frontend (e.g., `https://easypdf-frontend.vercel.app`). You can start with `*` for testing but it's less secure.

## 2. Frontend (Next.js) - Deploy to Vercel.com
1. Import your repository to Vercel.
2. **Environment Variables**:
    - `NEXT_PUBLIC_API_URL`: Add the URL of your deployed Backend (e.g., `https://easypdf-backend.onrender.com`).
3. Deploy!

## Notes
- Ensure your backend `requirements.txt` is up to date (`pip freeze > requirements.txt`).
- The backend needs to be deployed *first* so you can get its URL to put in the Frontend's environment variables.
