# VocaSense — Voice-Aware Hybrid AI Assistant
## Online Voice-Enabled Chatbot Using Speech Recognition and Deep Learning
### Technical Implementation Report for 20-Mark Lab Assessment

---

**Student Name:** Tanisha Bagga  
**Registration Number:** 23BAI0078  
**Program:** B.Tech CSE (AI & ML)  
**Institution:** Vellore Institute of Technology (VIT), Vellore  
**Course / Assessment:** Lab Assessment — Voice-Enabled Chatbot Development  

---

## 1. Abstract

VocaSense is an interactive, voice-enabled hybrid AI conversational chatbot system engineered to overcome the rigidity of traditional rule-based intent assistants. Built using client-side Web Speech APIs, a custom-trained 27-class Deep Learning model (Conv1D + Bidirectional LSTM), and OpenAI SDK generative AI integration, VocaSense processes both spoken voice input and written text queries in real time. The system captures voice through the browser's Web Speech API (`SpeechRecognition`), classifies intent and extracts key domain topics using an 84.38% test-accuracy BiLSTM neural network, and synthesizes open-domain natural language answers through Generative AI. Responses are displayed alongside transparent intent metadata, confidence scores, execution timelines, and optional Speech Synthesis audio output. The application includes complete deployment configuration files for hosting on Vercel.

---

## 2. Introduction

Voice-enabled conversational agents have transformed human-computer interaction by replacing manual text input with natural, friction-free voice commands. Traditional intent classification engines often fail when users express complex, multi-faceted queries (e.g., expressing hunger, exam stress, and a desire for entertainment in a single sentence). VocaSense bridges this gap by deploying a hybrid pipeline where a lightweight Deep Learning model performs rapid, accurate intent and topic classification, while a Large Language Model generates natural, contextually complete answers without being constrained to pre-written hardcoded responses.

---

## 3. Problem Statement

Most conventional voice assistants rely strictly on rigid intent-to-template response mappings. When a user input falls outside a narrow pre-programmed intent template, or when a user combines multiple intent categories into a single spoken query, traditional systems fail or return repetitive canned responses. There is a need for a voice-aware hybrid architecture that preserves fast Deep Learning intent detection while generating flexible, natural, and comprehensive AI answers.

---

## 4. Objectives

- **Accept Voice Input:** Capture user spoken voice input directly in the web browser using Web Speech `SpeechRecognition`.
- **Convert Speech to Text:** Convert spoken audio to text in real time and display the recognized transcript on the user interface.
- **Deep Learning Intent Classification:** Implement a Deep Learning model (`Conv1D` + `BiLSTM`) to classify input queries across 27 distinct intent categories.
- **Generative Response Generation:** Integrate Generative AI (via OpenAI SDK) to generate dynamic, unconstrained natural language answers based on user input and intent metadata.
- **Voice Output (TTS):** Provide text-to-speech audio feedback using Web Speech `SpeechSynthesis`.
- **Display Telemetry & Metrics:** Display execution telemetry including intent confidence percentages, model latency, and request IDs in an AI Analysis panel.
- **Prepare Vercel Deployment Configuration:** Prepare deployment configuration files for online hosting via Vercel serverless functions.

---

## 5. System Architecture

VocaSense follows a multi-tier pipeline designed for high responsiveness and transparent telemetry. The visual architecture flow is shown below:

```
Voice Input
    ↓
Speech Recognition
    ↓
Recognized Text
    ↓
Text Preprocessing
    ↓
Conv1D + BiLSTM
    ↓
Intent + Confidence
    ↓
Generative AI
    ↓
Response
    ↓
Text-to-Speech
```

### Component Details:
1. **Client Voice Input:** Captured via Web Speech API (`SpeechRecognition`) in `app/static/js/speech.js`.
2. **Speech Recognition:** Converts spoken microphone audio into text transcript.
3. **Recognized Text:** Displayed in real time in user chat bubble and text input bar.
4. **Text Preprocessing:** Lowercased, cleaned of punctuation, tokenized via `tokenizer.json`, and padded to `max_len = 15`.
5. **Conv1D + BiLSTM Model:** Keras Sequential model computes Softmax probabilities across 27 intent classes (84.38% test accuracy).
6. **Intent + Confidence:** Returns predicted intent tag (e.g. `JOKE_REQUEST`) and Softmax confidence score (0–100%).
7. **Generative AI:** OpenAI Python SDK wrapper sends raw query + intent metadata + conversation history to the configured API endpoint.
8. **Response:** Renders natural language response bubble with expandable timeline and technical verification accordions.
9. **Text-to-Speech:** Browser Web Speech Synthesis (`SpeechSynthesisUtterance`) provides voice audio output.

---

## 6. Dataset Documentation

The Deep Learning model was trained on a custom JSON dataset (`data/intents.json`) comprising 27 intent categories across 8 primary domain sectors.

| Metric / Parameter | Verified Numerical Value | Source File | Description |
|---|---|---|---|
| **Base Intent Classes** | 27 classes | `data/intents.json` | Intent categories spanning social, tech, academic, and campus topics |
| **Base Text Patterns** | 204 patterns | `data/intents.json` | Core human query patterns defined across intents |
| **Augmented Samples** | 635 samples | `data/train_test_split.json` | Generated via word-drop augmentation in `train.py` |
| **Training Set Size** | 443 samples (70%) | `data/train_test_split.json` | Used for model parameter optimization |
| **Validation Set Size** | 96 samples (15%) | `data/train_test_split.json` | Used for hyperparameter tuning & early stopping |
| **Test Set Size** | 96 samples (15%) | `data/train_test_split.json` | Held-out test set for final accuracy calculation |
| **Vocabulary Size** | 402 words | `data/train_test_split.json` | Unique tokens including `<OOV>` token |
| **Max Sequence Length** | 15 tokens | `data/train_test_split.json` | Post-padded/truncated sequence dimension |

### Verified Intent Categories (27 Classes):
`assignment_help`, `campus`, `casual_conversation`, `clubs`, `coding_practice`, `entertainment`, `events`, `exam_preparation`, `exam_stress`, `food_query`, `general_greeting`, `general_knowledge`, `goodbye`, `internship`, `interview`, `joke_request`, `library`, `motivation`, `productivity`, `programming`, `resume`, `science`, `study_help`, `study_plan`, `technology`, `thanks`, `weather`.

---

## 7. Data Preprocessing Pipeline

- **Text Normalization:** Input converted to lower case; punctuation removed using regex `re.sub(r"[^\w\s]", "", text)`.
- **Data Augmentation:** Sentence patterns with >3 words are augmented by systematically dropping single words to improve model robustness.
- **Tokenization:** Keras `Tokenizer` fits vocabulary (402 tokens) and converts text strings into sequence integers with `<OOV>` for out-of-vocabulary words.
- **Sequence Padding:** Sequences padded or truncated to fixed maximum length `max_len = 15` using post-padding.
- **Label Encoding:** Scikit-learn `LabelEncoder` maps 27 textual intent tags into class index integers (0 to 26).

---

## 8. Deep Learning Model Architecture

The intent classifier utilizes a hybrid Conv1D + Bidirectional LSTM architecture built with Keras Sequential API (`training/train.py`).

| Layer Type | Layer Configuration | Output Shape / Units | Functional Role |
|---|---|---|---|
| **Embedding** | `input_dim=402, output_dim=64, input_length=15` | `(None, 15, 64)` | Maps integer word indices to dense 64-D vectors |
| **SpatialDropout1D** | `rate=0.2` | `(None, 15, 64)` | Drops 20% feature channels to prevent co-adaptation |
| **Conv1D** | `filters=64, kernel_size=3, padding='same', relu` | `(None, 15, 64)` | Extracts local n-gram temporal features |
| **Bidirectional (LSTM)** | `units=64, return_sequences=True` | `(None, 15, 128)` | Learns forward & backward sequence context |
| **GlobalMaxPooling1D** | Max pooling over sequence time steps | `(None, 128)` | Extracts maximum salient feature signals |
| **Dense** | `units=64, activation='relu', L2 regularizer(0.001)` | `(None, 64)` | Dense feature projection with L2 regularization |
| **Dropout** | `rate=0.3` | `(None, 64)` | Prevents overfitting during training |
| **Dense (Output)** | `units=27, activation='softmax'` | `(None, 27)` | Computes probability distribution across 27 intents |

### Training Hyperparameters (Verified in `train.py`):
- **Optimizer:** `Adam(learning_rate = 0.003)`
- **Loss Function:** `sparse_categorical_crossentropy`
- **Batch Size:** `16`
- **Configured Epochs:** 40 (Early stopping triggered at epoch 23)
- **Callbacks:** `EarlyStopping(monitor='val_loss', patience=8)`, `ReduceLROnPlateau(factor=0.5, patience=3, min_lr=0.0001)`
- **Total Parameters:** `114,139` parameters

---

## 9. Speech Recognition Implementation

Speech Recognition is implemented client-side using the native W3C Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) in `app/static/js/speech.js`.

- **API Provider:** Native Web Speech API (supported in Google Chrome, Microsoft Edge, Safari).
- **Configuration:** `lang = 'en-US'`, `continuous = false`, `interimResults = false`.
- **Display Integration:** Spoken audio transcript is displayed in real time inside the user chat bubble and text input control bar.
- **Voice Synthesis Output:** Implemented via `window.speechSynthesis` (`SpeechSynthesisUtterance`) to read assistant answers aloud when TTS is enabled.

---

## 10. Chatbot & Response Generation Pipeline

VocaSense strictly distinguishes between intent classification and natural language response generation:

1. **BiLSTM Intent Model (Auxiliary Metadata):** Predicts intent tag, category, and confidence score. Does NOT lock the system to canned responses.
2. **Generative AI SDK Integration (`app.py`):** Uses official `openai` Python SDK (`OpenAI`) to initialize client connection based on configured environment variables:
   - **Groq Cloud API Endpoint:** Uses base URL `https://api.groq.com/openai/v1` with model `openai/gpt-oss-20b` when initialized with a `gsk_` API key prefix.
   - **xAI Grok API Endpoint:** Uses base URL `https://api.x.ai/v1` with model `grok-2-latest` when initialized with an `xai-` API key prefix.
3. **System Prompting:** Receives raw user text + predicted intent + confidence % + extracted topics + up to 6 turns of conversation history.
4. **Intelligent Offline Fallback:** If API key is unconfigured or network fails, `app.py` uses a rule-based intelligent fallback generator.

---

## 11. User Interface & Key Features

- **Soft Pastel Iridescent Theme:** Ambient blurred aurora background blobs (`#f8fafc` light, `#0b0f19` dark mode) with glassmorphism cards.
- **Header Controls:** Home button, AI Analysis drawer toggle, Voice Output (TTS) toggle, Light/Dark Theme toggle, and BiLSTM + Grok Tech Modal button.
- **Home / Welcome Screen:** Prominently displays `VocaSense — Voice-Aware Hybrid AI Assistant` and subtitle `Speak naturally. Ask anything.`, alongside "How It Works" pipeline flow and "Core Capabilities" cards.
- **Demo Discovery Cards:** 5 clickable prompt discovery cards with vector icons (Quantum Computing, Joke, Bored & Hungry, Python Fibonacci, Interview Prep).
- **Topic Filter Chips:** Category pills (All, Daily Life, Programming, Science & Tech, Exam Prep) that filter demo cards in real time.
- **Expandable Accordions:** Every assistant message bubble includes "Processing Timeline" (STT, ML, Grok, Total backend timing in ms) and "Technical Details" (Request ID, model metadata).

---

## 12. Results and Performance Evaluation

Model evaluation was conducted on the held-out test set (96 samples) using `model/evaluation_metrics.json`:

| Evaluation Metric | Verified Numerical Value | Percentage |
|---|---|---|
| **Test Set Accuracy** | `0.843750` | **84.38%** |
| **Weighted Precision** | `0.879390` | **87.94%** |
| **Weighted Recall** | `0.843750` | **84.38%** |
| **Weighted F1-Score** | `0.841452` | **84.15%** |
| **Total Model Parameters** | `114,139` | **114.1K Params** |
| **Training Epochs Completed** | `23 epochs` | **Stopped at Epoch 23** |

---

## 13. Local & Automated Verification Testing

Verification tests executed against local application instance (recorded in `scratch/verification_tests.py`):

| Test Case ID & Description | Expected Result | Actual Verified Result | Status |
|---|---|---|---|
| **TC-01: App Initialization** | Primary chat prominent, analytics drawer collapsed | Chat UI loaded as primary view; drawer closed | **PASS** |
| **TC-02: Voice Input STT** | Voice captured via microphone and rendered | SpeechRecognition transcript displayed in user bubble | **PASS** |
| **TC-03: Single Query Processing** | Predicts intent and generates AI response | Returned Request ID VS-20260923-001 in 1059 ms | **PASS** |
| **TC-04: Multi-Aspect Query** | Addresses food, exam, stress, and boredom | Generated multi-faceted step-by-step advice | **PASS** |
| **TC-05: Concurrency Guard** | Blocks duplicate clicks during processing | `isProcessing` flag prevented duplicate API requests | **PASS** |
| **TC-06: Code Generation Query** | Generates clean Python code for sorting | Returned formatted Python list sorting code snippet | **PASS** |
| **TC-07: Offline Fallback Mode** | Generates intelligent answer if API key missing | Fallback generator executed without crashing server | **PASS** |
| **TC-08: Health Check Endpoint** | GET /health returns JSON status | Returned status: healthy, model_loaded: true | **PASS** |

---

## 14. Vercel Deployment Configuration

The application is fully prepared and configured for online deployment using Vercel serverless functions:

- **Serverless Functions:** `vercel.json` routes API endpoints `/api/chat` and `/health` to `app.py` using `@vercel/python`.
- **Static Asset Routing:** `/static/` assets mapped to `/app/static/`.
- **WSGI Entrypoint:** `api/index.py` imports `app` for Vercel serverless functions.
- **WSGI Production Backup:** `Procfile` configured for Gunicorn deployment (`web: gunicorn app:app`).
- **Environment Security:** `GROK_API_KEY` stored securely via environment variables; never exposed to frontend code.
- **Deployment Status:** Vercel deployment configuration files are complete. The public deployment URL will be updated upon final deployment.

---

## 15. Limitations & Future Work

### Limitations:
- Speech Recognition depends on browser support for Web Speech API (Chrome, Edge, Safari).
- Generative AI latency depends on external network ping and API rate limits.
- Dataset currently contains 27 intent classes; expanding intent classes will improve niche domain coverage.

### Future Enhancements:
- Multilingual Speech Recognition & Synthesis for multi-language voice conversations.
- Local Whisper / Vosk STT engine fallback for offline voice recognition without browser API dependency.
- Enhanced session persistence with database-backed conversation history.

---

## 16. Conclusion

VocaSense successfully fulfills all requirements for the 20-mark Lab Assessment. The application incorporates browser-native speech recognition to convert voice to text, a custom-trained 27-class Conv1D + BiLSTM Deep Learning model (84.38% test accuracy) for intent classification, Generative AI integration for open-domain response generation, and Speech Synthesis for audio playback. The application features a soft pastel glassmorphic user interface and is prepared with Vercel deployment configuration.

---

## 17. Requirement Traceability Table

| Faculty Assessment Requirement | VocaSense Implementation | Verification Evidence |
|---|---|---|
| **1. Speech Recognition** | Web Speech API integration in `speech.js` | Mic button triggers WebSpeech STT transcript capture |
| **2. Deep Learning Model** | 27-class Conv1D + BiLSTM in `train.py` & `app.py` | `intent_model.keras` (84.38% test accuracy) |
| **3. Display Recognized Speech** | Real-time transcript rendered in chat bubble | User bubble & text input display captured text |
| **4. Display Chatbot Response** | Generative AI natural language answer rendering | Bot message bubble with formatted text & code blocks |
| **5. Voice Output (TTS)** | Web Speech Synthesis API in `speech.js` | `ttsToggleBtn` enables `SpeechSynthesisUtterance` audio |
| **6. Online Deployment Config** | Vercel serverless config (`vercel.json`, `api/index.py`) | Serverless deployment files & `Procfile` configured |
| **7. Source Code & Documentation** | Complete Flask application codebase & report | All files verified in project directory |

---

## 18. Verified Technical Values

- **Accuracy:** `84.38%` (`0.84375`)
- **Weighted Precision:** `87.94%` (`0.87938988`)
- **Weighted Recall:** `84.38%` (`0.84375`)
- **Weighted F1-Score:** `84.15%` (`0.84145171`)
- **Model Parameters:** `114,139`
- **Training Epochs:** `23` (Early stopping triggered at epoch 23 of 40)
- **Dataset Size:** `635` total augmented samples (443 train, 96 val, 96 test)
- **Vocabulary Size:** `402` words
- **Max Sequence Length:** `15` tokens
- **Number of Classes:** `27` intent categories
- **Optimizer:** `Adam(learning_rate=0.003)`
- **Loss Function:** `sparse_categorical_crossentropy`
- **Batch Size:** `16`

---

## 19. Unverifiable Values (Explicitly Not Fabricated)

- **Browser Audio Sample Rate:** Varies depending on user microphone hardware and OS audio driver; not fixed in source code.
- **Exact Generative AI Infrastructure Latency:** Varies dynamically depending on external server load and network ping.
- **Specific Live Deployment Domain URL:** Depends on the student's personal Vercel deployment instance name upon final deployment.

---

## 20. Project Files Inspected

1. `app.py`
2. `app/templates/index.html`
3. `app/static/css/style.css`
4. `app/static/js/app.js`
5. `app/static/js/speech.js`
6. `training/train.py`
7. `data/intents.json`
8. `data/train_test_split.json`
9. `model/evaluation_metrics.json`
10. `model/intent_metadata.json`
11. `model/label_encoder.json`
12. `model/tokenizer.json`
13. `scratch/verification_tests.py`
14. `vercel.json`
15. `api/index.py`
16. `Procfile`
17. `requirements.txt`
