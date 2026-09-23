/* VocaSense - Web Speech API Handler (STT & TTS) */

class SpeechHandler {
    constructor(options = {}) {
        this.onResultCallback = options.onResult || null;
        this.onStateChangeCallback = options.onStateChange || null;
        this.onErrorCallback = options.onError || null;

        this.recognition = null;
        this.synthesis = window.speechSynthesis || null;
        this.isListening = false;
        this.ttsEnabled = true;

        this.initRecognition();
    }

    initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.warn("[VocaSense] Web Speech Recognition API is not supported in this browser.");
            if (this.onErrorCallback) {
                this.onErrorCallback("Web Speech API is not supported in your browser. Please use Chrome, Edge, or Safari.");
            }
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.sttStartTime = null;

        this.recognition.onstart = () => {
            this.isListening = true;
            this.sttStartTime = performance.now();
            if (this.onStateChangeCallback) this.onStateChangeCallback('LISTENING');
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const sttDurationMs = (finalTranscript && this.sttStartTime) ? Math.round(performance.now() - this.sttStartTime) : null;

            if (this.onResultCallback) {
                this.onResultCallback({
                    interim: interimTranscript,
                    final: finalTranscript,
                    sttDurationMs: sttDurationMs
                });
            }
        };

        this.recognition.onerror = (event) => {
            console.error("[VocaSense Speech Error]", event.error);
            this.isListening = false;
            if (this.onStateChangeCallback) this.onStateChangeCallback('IDLE');

            let errorMessage = "Microphone error occurred.";
            if (event.error === 'not-allowed' || event.error === 'permission-denied') {
                errorMessage = "Microphone permission denied. Please allow microphone access in your browser settings.";
            } else if (event.error === 'no-speech') {
                errorMessage = "No speech detected. Please try speaking again clearly.";
            } else if (event.error === 'audio-capture') {
                errorMessage = "No microphone hardware detected on your device.";
            }

            if (this.onErrorCallback) this.onErrorCallback(errorMessage);
        };

        this.recognition.onend = () => {
            this.isListening = false;
            if (this.onStateChangeCallback) this.onStateChangeCallback('IDLE');
        };
    }

    toggleListening() {
        if (!this.recognition) {
            alert("Web Speech API is not supported in your browser. Please type your message below!");
            return;
        }

        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    startListening() {
        if (this.recognition && !this.isListening) {
            try {
                // Cancel any ongoing speech synthesis before listening
                if (this.synthesis) this.synthesis.cancel();
                this.recognition.start();
            } catch (err) {
                console.error("Failed to start speech recognition:", err);
            }
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    speak(text) {
        if (!this.synthesis || !this.ttsEnabled || !text) return;

        // Cancel previous utterances
        this.synthesis.cancel();

        const cleanTextToSpeak = text.replace(/<[^>]*>/g, '').replace(/[^\w\s.,?!']/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanTextToSpeak);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.lang = 'en-US';

        utterance.onstart = () => {
            if (this.onStateChangeCallback) this.onStateChangeCallback('RESPONDING');
        };

        utterance.onend = () => {
            if (this.onStateChangeCallback) this.onStateChangeCallback('IDLE');
        };

        utterance.onerror = () => {
            if (this.onStateChangeCallback) this.onStateChangeCallback('IDLE');
        };

        this.synthesis.speak(utterance);
    }

    toggleTTS() {
        this.ttsEnabled = !this.ttsEnabled;
        if (!this.ttsEnabled && this.synthesis) {
            this.synthesis.cancel();
        }
        return this.ttsEnabled;
    }
}
