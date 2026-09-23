import os
import json
import re
import random
import time
import uuid
from datetime import datetime
import numpy as np
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

try:
    import tensorflow as tf
    from tensorflow.keras.preprocessing.text import tokenizer_from_json
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    TF_AVAILABLE = True
except Exception as e:
    print(f"[SERVER WARNING] TensorFlow not available or failed to load: {e}")
    TF_AVAILABLE = False
    tf = None

REQUEST_COUNTER = 0

# Load Environment Variables from .env
load_dotenv()

base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, "app", "templates"),
            static_folder=os.path.join(base_dir, "app", "static"))
CORS(app)

# Grok / Groq API Configuration
GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-latest").strip()

GROK_CLIENT = None
def init_grok_client():
    global GROK_CLIENT, GROK_API_KEY, GROK_MODEL
    GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip()
    user_model = os.getenv("GROK_MODEL", "").strip()
    
    if GROK_API_KEY and not GROK_API_KEY.startswith("xai-YOUR_"):
        try:
            from openai import OpenAI
            if GROK_API_KEY.startswith("gsk_"):
                base_url = "https://api.groq.com/openai/v1"
                GROK_MODEL = user_model if (user_model and not user_model.startswith("grok-")) else "openai/gpt-oss-20b"
                service_name = "Groq AI"
            else:
                base_url = "https://api.x.ai/v1"
                GROK_MODEL = user_model if user_model else "grok-2-latest"
                service_name = "Grok AI"

            GROK_CLIENT = OpenAI(
                api_key=GROK_API_KEY,
                base_url=base_url
            )
            print(f"[SERVER] Initialized {service_name} API client successfully (base_url: {base_url}, model: {GROK_MODEL}).")
        except Exception as e:
            print(f"[WARNING] Failed to initialize AI client: {e}")
            GROK_CLIENT = None
    else:
        print("[SERVER] API Key is not set or using placeholder. Fallback AI response generator active.")

# Global ML artifacts
MODEL = None
TOKENIZER = None
LABEL_CLASSES = None
MAX_LEN = 15
METADATA = {}

def load_ml_artifacts():
    global MODEL, TOKENIZER, LABEL_CLASSES, MAX_LEN, METADATA
    model_dir = os.path.join(base_dir, "model")
    
    model_path = os.path.join(model_dir, "intent_model.keras")
    tokenizer_path = os.path.join(model_dir, "tokenizer.json")
    encoder_path = os.path.join(model_dir, "label_encoder.json")
    metadata_path = os.path.join(model_dir, "intent_metadata.json")
    
    if TF_AVAILABLE and os.path.exists(model_path):
        try:
            MODEL = tf.keras.models.load_model(model_path)
            print("[SERVER] Loaded BiLSTM Keras model successfully.")
        except Exception as e:
            print(f"[WARNING] Failed to load Keras model: {e}")
            MODEL = None
    else:
        print("[SERVER NOTICE] Running in lightweight/serverless mode without Keras model.")
        
    if TF_AVAILABLE and os.path.exists(tokenizer_path):
        try:
            with open(tokenizer_path, "r", encoding="utf-8") as f:
                TOKENIZER = tokenizer_from_json(f.read())
            print("[SERVER] Loaded Tokenizer config.")
        except Exception as e:
            TOKENIZER = None
        
    if os.path.exists(encoder_path):
        with open(encoder_path, "r", encoding="utf-8") as f:
            enc_data = json.load(f)
            LABEL_CLASSES = enc_data["classes"]
            MAX_LEN = enc_data.get("max_len", 15)
        print("[SERVER] Loaded Label Encoder classes.")
    else:
        LABEL_CLASSES = ["casual_conversation", "joke_request", "food_query", "exam_stress", "general_greeting", "goodbye", "thanks"]
        
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            METADATA = json.load(f)
        print("[SERVER] Loaded Intent Metadata.")

def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return text

def extract_detected_topics(text):
    """
    Extract key multi-aspect topics from user text (e.g. food, exam, stress, boredom, code, etc.)
    """
    cleaned = text.lower()
    topics = []
    
    keyword_map = {
        "hungry": "food & eating",
        "food": "food & eating",
        "eat": "food & eating",
        "dinner": "food & eating",
        "lunch": "food & eating",
        "exam": "exams & test prep",
        "test": "exams & test prep",
        "finals": "exams & test prep",
        "study": "studying & revision",
        "stressed": "stress management",
        "anxious": "anxiety relief",
        "panic": "stress relief",
        "bored": "boredom & entertainment",
        "joke": "jokes & humor",
        "code": "programming",
        "python": "Python programming",
        "quantum": "quantum computing",
        "weather": "weather forecast",
        "rain": "weather & rain",
        "interview": "interview prep",
        "job": "career & jobs",
        "resume": "resume building",
        "travel": "travel & trip planning"
    }
    
    for kw, topic in keyword_map.items():
        if kw in cleaned and topic not in topics:
            topics.append(topic)
            
    return topics

def generate_grok_response(user_text, predicted_intent, confidence_pct, detected_topics, conversation_history):
    """
    Sends ORIGINAL user text + conversation history + system prompt to Grok API.
    """
    if GROK_CLIENT is None:
        return None, None
        
    topics_str = ", ".join(detected_topics) if detected_topics else "General"
    
    system_prompt = f"""You are VocaSense, a general-purpose conversational AI voice assistant.

Your primary job is to understand and directly answer the user's ACTUAL user message.

AUXILIARY DEEP LEARNING MODEL ANALYSIS:
- Primary Predicted Intent: {predicted_intent}
- Model Confidence: {confidence_pct}%
- Detected Key Topics: {topics_str}

CRITICAL SYSTEM INSTRUCTION:
The Deep Learning intent classifier is an auxiliary metadata tool and may occasionally be incomplete or incorrect.
NEVER let the predicted intent restrict or override what the user actually said.

- Analyze the COMPLETE user message yourself.
- If the user mentions MULTIPLE concerns or questions in one sentence (e.g., feeling bored, having an upcoming exam, feeling stressed, AND being hungry), address ALL their concerns in a warm, direct, step-by-step conversational answer!
- If the user asks a technical or coding question ("Write a Python program for sorting", "Explain TCP vs UDP"), provide clear explanations or clean code snippets.
- If the user asks for a joke, creative writing, general knowledge, science, travel, or finance advice, fulfill it directly.
- Keep responses conversational, helpful, and concise (typically 2-4 sentences unless code or step-by-step guidance is specifically requested).
- Do not mention internal ML intent classification numbers or intent tags in your response text unless the user explicitly asks how VocaSense works."""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add recent conversation history (up to last 6 turns)
    if isinstance(conversation_history, list):
        for msg in conversation_history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"] and content:
                messages.append({"role": role, "content": content})
                
    messages.append({"role": "user", "content": user_text})
    
    try:
        t0 = time.perf_counter()
        response = GROK_CLIENT.chat.completions.create(
            model=GROK_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        t1 = time.perf_counter()
        grok_api_ms = round((t1 - t0) * 1000, 2)
        reply = response.choices[0].message.content.strip()
        return reply, grok_api_ms
    except Exception as e:
        print(f"[ERROR] Grok API call failed: {e}")
        return None, None

def generate_offline_fallback_response(user_text, detected_topics, predicted_intent):
    """
    Intelligent dynamic response generator when GROK_API_KEY is not configured.
    Never returns a canned "I classified your request as..." meta-sentence.
    """
    cleaned = user_text.lower()
    
    # Handle multi-aspect user requests (e.g. bored + exam + stressed + hungry)
    if "hungry" in cleaned or "eat" in cleaned or "food" in cleaned:
        if "exam" in cleaned or "stress" in cleaned or "bored" in cleaned:
            return "You've got a few things happening at once! First, grab a quick healthy bite to eat to fuel your brain. Next, take a 5-minute breather to lower your stress, then pick just ONE core exam topic to focus on for 25 minutes. Taking it step by step will make studying feel much less overwhelming!"
        return "Sounds like it's time for some food! Grab a quick snack like fruit, nuts, or a sandwich to get your energy back up!"

    if "joke" in cleaned:
        jokes = [
            "Why did the programmer quit his job? Because he didn't get arrays! 😄",
            "Why do scientists trust atoms? Because they make up everything! ⚛️",
            "Why was the computer cold? It left its Windows open! 💻"
        ]
        return random.choice(jokes)

    if "quantum" in cleaned:
        return "Quantum computing uses quantum bits (qubits) that can exist as 0, 1, or both simultaneously (superposition). This allows quantum computers to process complex calculations exponentially faster than classical computers!"

    if "sort" in cleaned or "python" in cleaned or "code" in cleaned:
        return "Here is how you can sort a list in Python:\n```python\n# Using built-in sort\nnumbers = [5, 2, 9, 1, 7]\nnumbers.sort()\nprint('Sorted list:', numbers) # [1, 2, 5, 7, 9]\n```"

    if "exam" in cleaned or "stress" in cleaned:
        return "Take a deep breath! Stress reduces memory retention. Break your revision into 25-minute Pomodoro focus blocks with 5-minute breaks, stay hydrated, and focus on high-priority topics first."

    if "bored" in cleaned:
        return "Whenever you feel bored, try switching tasks! You could learn a 5-minute fun tech concept, try a quick coding puzzle, or go for a brisk walk to reset your mind."

    # Intent domain fallbacks (Never meta-sentences!)
    intent_fallback_map = {
        "joke_request": "Why don't programmers like nature? It has too many bugs! 😄",
        "food_query": "If you're looking for food ideas, try a quick 15-minute pasta dish or a fresh Mediterranean salad!",
        "exam_stress": "Take a 2-minute pause. Inhale slowly for 4 seconds, hold for 4, and exhale for 4. Now focus on just one chapter summary.",
        "general_greeting": "Hello! I am VocaSense. I'm ready to answer any questions across coding, science, fitness, career, travel, and more!",
        "goodbye": "Goodbye! Have a great day ahead and feel free to ask questions anytime!",
        "thanks": "You're very welcome! I'm glad I could help."
    }
    
    return intent_fallback_map.get(predicted_intent, f"I'm here to help you with '{user_text}'. What specific details would you like to explore?")

def heuristic_intent_predict(text):
    cleaned = text.lower()
    if any(k in cleaned for k in ["joke", "funny", "laugh", "humor"]):
        tag = "joke_request"
        conf = 0.98
    elif any(k in cleaned for k in ["hungry", "food", "eat", "dinner", "lunch", "restaurant"]):
        tag = "food_query"
        conf = 0.95
    elif any(k in cleaned for k in ["exam", "stress", "anxious", "test", "study", "prep"]):
        tag = "exam_stress"
        conf = 0.96
    elif any(k in cleaned for k in ["hi", "hello", "hey", "greetings"]):
        tag = "general_greeting"
        conf = 0.99
    elif any(k in cleaned for k in ["bye", "goodbye", "see ya"]):
        tag = "goodbye"
        conf = 0.99
    elif any(k in cleaned for k in ["thanks", "thank you"]):
        tag = "thanks"
        conf = 0.99
    else:
        tag = "casual_conversation"
        conf = 0.92
    return tag, conf, [{"intent": tag, "confidence": conf}]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "VocaSense AI Assistant",
        "model_loaded": MODEL is not None,
        "grok_api_active": GROK_CLIENT is not None,
        "grok_model": GROK_MODEL
    })

@app.route("/predict", methods=["POST"])
@app.route("/api/chat", methods=["POST"])
def predict():
    global REQUEST_COUNTER
    req_start = time.perf_counter()
    
    if (MODEL is None or TOKENIZER is None or LABEL_CLASSES is None) and TF_AVAILABLE:
        load_ml_artifacts()
    
    if GROK_CLIENT is None:
        init_grok_client()

    data = request.get_json() or {}
    user_text = data.get("message") or data.get("text") or ""
    user_text = user_text.strip()
    history = data.get("conversation_history", [])
    
    if not user_text:
        return jsonify({"error": "No text input provided"}), 400

    REQUEST_COUNTER += 1
    req_date = datetime.now().strftime("%Y%m%d")
    request_id = f"VS-{req_date}-{REQUEST_COUNTER:03d}"

    print(f"\n[1] [{request_id}] Received user message: '{user_text}'")
    
    cleaned = clean_text(user_text)
    tokens = cleaned.split()
    
    # 1. Intent Classification (Deep Learning or Heuristic Serverless Fallback)
    t_ml_start = time.perf_counter()
    if MODEL is not None and TOKENIZER is not None and LABEL_CLASSES is not None:
        seq = TOKENIZER.texts_to_sequences([cleaned])
        padded = pad_sequences(seq, maxlen=MAX_LEN, padding="post", truncating="post")
        probs = MODEL.predict(padded, verbose=0)[0]
        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])
        predicted_tag = LABEL_CLASSES[pred_idx]
        confidence_pct = round(confidence * 100, 1)
        top_indices = np.argsort(probs)[::-1][:3]
        top_intents = [
            {"intent": LABEL_CLASSES[i], "confidence": round(float(probs[i]), 4)}
            for i in top_indices
        ]
    else:
        predicted_tag, confidence, top_intents = heuristic_intent_predict(user_text)
        confidence_pct = round(confidence * 100, 1)

    t_ml_end = time.perf_counter()
    ml_inference_ms = round((t_ml_end - t_ml_start) * 1000, 2)
    
    print(f"[2] [{request_id}] ML classifier executed in {ml_inference_ms} ms.")
    print(f"[3] [{request_id}] ML predicted intent = {predicted_tag.upper()}")
    print(f"[4] [{request_id}] ML confidence = {confidence:.4f} ({confidence_pct}%)")
    
    # Detect multi-aspect topics
    detected_topics = extract_detected_topics(user_text)
    print(f"[4.1] [{request_id}] Detected Key Topics = {detected_topics}")

    # Top 3 intents for visualization
    top_indices = np.argsort(probs)[::-1][:3]
    top_intents = [
        {"intent": LABEL_CLASSES[i], "confidence": round(float(probs[i]), 4)}
        for i in top_indices
    ]
    
    intent_meta = METADATA.get(predicted_tag, {})
    category = intent_meta.get("category", "General Inquiry")

    # 2. Response Generation via Grok API (Measured Timing)
    print(f"[5] [{request_id}] Calling Grok API (model: {GROK_MODEL})...")
    grok_reply, grok_api_ms = generate_grok_response(user_text, predicted_tag, confidence_pct, detected_topics, history)
    
    if grok_reply:
        print(f"[6] [{request_id}] Grok API response received in {grok_api_ms} ms!")
        response_text = grok_reply
        response_mode = "GROK_AI"
        response_engine_name = f"Grok AI ({GROK_MODEL})"
    else:
        print(f"[5.1] [{request_id}] Grok API Key is missing or call failed. Using Intelligent Fallback Response Generator...")
        response_text = generate_offline_fallback_response(user_text, detected_topics, predicted_tag)
        response_mode = "FALLBACK_AI"
        response_engine_name = "Intelligent AI Generator"
        grok_api_ms = None

    total_backend_ms = round((time.perf_counter() - req_start) * 1000, 2)
    print(f"[7] [{request_id}] Returning response to frontend (Total backend time: {total_backend_ms} ms).\n")

    suggested_action = intent_meta.get("suggested_action", "Explore related topics or ask another question.")
    
    why_this_response = {
        "request_id": request_id,
        "recognized_text": user_text,
        "tokens": tokens,
        "predicted_intent": predicted_tag.upper(),
        "confidence_pct": f"{confidence_pct}%",
        "category": category,
        "detected_topics": detected_topics if detected_topics else [category],
        "response_engine": response_engine_name,
        "mode": response_mode,
        "ml_model_name": "intent_model.keras (Conv1D + BiLSTM)",
        "grok_model_name": GROK_MODEL,
        "grok_connected": GROK_CLIENT is not None,
        "ml_inference_ms": ml_inference_ms,
        "grok_api_ms": grok_api_ms,
        "total_backend_ms": total_backend_ms
    }
    
    return jsonify({
        "request_id": request_id,
        "recognized_text": user_text,
        "text": user_text,
        "message": user_text,
        "intent": predicted_tag,
        "confidence": round(confidence, 4),
        "confidence_pct": confidence_pct,
        "response": response_text,
        "suggested_action": suggested_action,
        "category": category,
        "detected_topics": detected_topics,
        "response_mode": response_mode,
        "response_engine": response_engine_name,
        "top_intents": top_intents,
        "ml_inference_ms": ml_inference_ms,
        "grok_api_ms": grok_api_ms,
        "total_backend_ms": total_backend_ms,
        "why_this_response": why_this_response
    })

# Initialize artifacts and API client on import (WSGI/Vercel compatibility)
load_ml_artifacts()
init_grok_client()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
