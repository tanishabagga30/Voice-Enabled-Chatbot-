# Deployment Guide — VocaSense Hybrid AI Assistant

This document provides step-by-step instructions for deploying **VocaSense — Voice-Aware Hybrid AI Assistant** to public cloud platforms.

> [!IMPORTANT]
> **1. HTTPS Requirement for Microphone Access**
> Web Speech API (`SpeechRecognition`) requires a secure **HTTPS** context in modern browsers (Chrome, Edge, Safari). All recommended platforms below automatically supply free SSL/TLS HTTPS certificates out of the box.
>
> **2. Setting `GROK_API_KEY` Environment Variable**
> On your deployment platform, add an Environment Variable named `GROK_API_KEY` containing your Grok API key (`xai-...`).

---

## Option 1: Render.com (Recommended Free Web Service)

Render provides free hosting for Flask applications with automatic HTTPS.

### Steps:
1. **Push Code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "VocaSense Hybrid AI release"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/vocasense.git
   git push -u origin main
   ```
2. **Log into Render**:
   - Go to [render.com](https://render.com) and click **New + → Web Service**.
   - Connect your GitHub repository `vocasense`.
3. **Configure Build Settings**:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. **Environment Variables**:
   - Add Key: `GROK_API_KEY`, Value: `xai-YOUR_API_KEY_HERE`
   - Add Key: `GROK_MODEL`, Value: `grok-2-latest`
5. **Deploy**:
   - Click **Create Web Service**. Render will deploy your public URL (e.g., `https://vocasense.onrender.com`).

---

## Option 2: Hugging Face Spaces (Docker / Flask Space)

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Select SDK: **Docker**.
3. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.10-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 7860
   CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
   ```
4. In Space Settings → **Variables and secrets**, add secret `GROK_API_KEY`.

---

## Local Verification Before Deployment

To verify local server startup:
```bash
python app.py
```
Open `http://localhost:5000` in your web browser.
