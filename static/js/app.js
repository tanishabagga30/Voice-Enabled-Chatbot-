/* VocaSense — Voice-Aware AI Assistant Controller */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const micBtn = document.getElementById('micBtn');
    const textInput = document.getElementById('textInput');
    const sendBtn = document.getElementById('sendBtn');
    
    const chatViewport = document.getElementById('chatViewport');
    const chatMessages = document.getElementById('chatMessages');
    const welcomeCard = document.getElementById('welcomeCard');
    
    const homeBtn = document.getElementById('homeBtn');
    const startTalkingBtn = document.getElementById('startTalkingBtn');
    const quickVoiceCard = document.getElementById('quickVoiceCard');
    const quickGrokCard = document.getElementById('quickGrokCard');
    
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const listeningWaveform = document.getElementById('listeningWaveform');
    
    const toggleAnalyticsBtn = document.getElementById('toggleAnalyticsBtn');
    const analyticsDrawer = document.getElementById('analyticsDrawer');
    const analyticsChevron = document.getElementById('analyticsChevron');
    
    const statMessages = document.getElementById('statMessages');
    const statVoiceInputs = document.getElementById('statVoiceInputs');
    const statTopIntent = document.getElementById('statTopIntent');
    const statAvgConf = document.getElementById('statAvgConf');
    
    const metaIntent = document.getElementById('metaIntent');
    const metaConf = document.getElementById('metaConf');
    const metaGrok = document.getElementById('metaGrok');
    const metaReqId = document.getElementById('metaReqId');
    
    const tTimeSTT = document.getElementById('tTimeSTT');
    const tTimeML = document.getElementById('tTimeML');
    const tTimeGrok = document.getElementById('tTimeGrok');
    const tTimeTotal = document.getElementById('tTimeTotal');
    
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const ttsToggleBtn = document.getElementById('ttsToggleBtn');
    
    // Concurrency Control & State Management
    let isProcessing = false;
    let currentSTTDurationMs = null;

    let sessionState = {
        totalMessages: 0,
        voiceInputsCount: 0,
        intentsCount: {},
        confidenceScores: [],
        conversationHistory: []
    };

    // State Machine: IDLE | LISTENING | PROCESSING | RESPONDING
    function setSystemState(state) {
        if (!statusDot || !statusText) return;
        
        statusDot.className = 'status-dot ' + state.toLowerCase();
        
        if (state === 'LISTENING') {
            isProcessing = true;
            statusText.textContent = 'LISTENING — Speak into your microphone now...';
            if (listeningWaveform) listeningWaveform.style.display = 'flex';
            toggleControls(false);
        } else if (state === 'PROCESSING') {
            isProcessing = true;
            statusText.textContent = 'PROCESSING — Analyzing → Understanding → Generating response...';
            if (listeningWaveform) listeningWaveform.style.display = 'none';
            toggleControls(false);
        } else if (state === 'RESPONDING') {
            isProcessing = true;
            statusText.textContent = 'RESPONDING — Voice synthesis output playing...';
            if (listeningWaveform) listeningWaveform.style.display = 'none';
            toggleControls(false);
        } else {
            // IDLE
            isProcessing = false;
            statusText.textContent = 'IDLE — Ready for voice or text';
            if (listeningWaveform) listeningWaveform.style.display = 'none';
            toggleControls(true);
        }
    }

    // Enable/Disable Controls during processing
    function toggleControls(enable) {
        const disabled = !enable;
        if (sendBtn) sendBtn.disabled = disabled;
        if (textInput) textInput.disabled = disabled;
        if (micBtn) micBtn.disabled = disabled;
        if (startTalkingBtn) startTalkingBtn.disabled = disabled;
        
        document.querySelectorAll('.prompt-chip, .discover-card').forEach(chip => {
            chip.disabled = disabled;
        });
    }

    // Speech Handler Instance
    const speech = new SpeechHandler({
        onResult: (data) => {
            if (data.final) {
                currentSTTDurationMs = data.sttDurationMs || null;
                handleUserQuery(data.final, true);
            }
        },
        onStateChange: (state) => {
            setSystemState(state);
        },
        onError: (errorMsg) => {
            console.warn("[Speech Notice]", errorMsg);
            setSystemState('IDLE');
        }
    });

    // Home Button & Avatar Pill Click Handler (Return to Welcome Screen)
    const avatarHomeBtn = document.getElementById('avatarHomeBtn') || document.querySelector('.user-avatar-pill');
    if (avatarHomeBtn) {
        avatarHomeBtn.style.cursor = 'pointer';
        avatarHomeBtn.addEventListener('click', () => {
            if (welcomeCard) welcomeCard.style.display = 'flex';
            if (chatViewport) chatViewport.scrollTop = 0;
        });
    }

    if (homeBtn) {
        homeBtn.addEventListener('click', () => {
            if (welcomeCard) {
                welcomeCard.style.display = 'flex';
            }
            if (chatViewport) {
                chatViewport.scrollTop = 0;
            }
        });
    }

    // Tech Architecture Modal Handler
    const techBadgeBtn = document.getElementById('techBadgeBtn');
    const techModal = document.getElementById('techModal');
    const closeTechModalBtn = document.getElementById('closeTechModalBtn');

    if (techBadgeBtn && techModal) {
        techBadgeBtn.addEventListener('click', () => {
            techModal.classList.add('active');
        });
    }

    if (closeTechModalBtn && techModal) {
        closeTechModalBtn.addEventListener('click', () => {
            techModal.classList.remove('active');
        });
    }

    if (techModal) {
        techModal.addEventListener('click', (e) => {
            if (e.target === techModal) {
                techModal.classList.remove('active');
            }
        });
    }

    // Toggle Collapsible Analytics Drawer
    if (toggleAnalyticsBtn && analyticsDrawer) {
        toggleAnalyticsBtn.addEventListener('click', () => {
            analyticsDrawer.classList.toggle('collapsed');
            if (analyticsChevron) {
                analyticsChevron.classList.toggle('fa-chevron-down');
                analyticsChevron.classList.toggle('fa-chevron-up');
            }
        });
    }

    // Start Talking Button & Quick Cards
    if (startTalkingBtn) {
        startTalkingBtn.addEventListener('click', () => {
            if (isProcessing) return;
            speech.toggleListening();
        });
    }

    if (quickVoiceCard) {
        quickVoiceCard.addEventListener('click', () => {
            if (isProcessing) return;
            speech.toggleListening();
        });
    }

    if (quickGrokCard) {
        quickGrokCard.addEventListener('click', () => {
            if (isProcessing) return;
            currentSTTDurationMs = null;
            handleUserQuery("Explain how Grok AI and BiLSTM work in VocaSense", false);
        });
    }

    // Microphone Click Handler
    if (micBtn) {
        micBtn.addEventListener('click', () => {
            if (isProcessing) return;
            speech.toggleListening();
        });
    }

    // Send Button Click Handler
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            if (isProcessing) return;
            const text = textInput.value.trim();
            if (text) {
                currentSTTDurationMs = null;
                handleUserQuery(text, false);
                textInput.value = '';
            }
        });
    }

    // Enter Key Handler
    if (textInput) {
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendBtn.click();
            }
        });
    }

    // Topic Filter Pills Handler
    document.querySelectorAll('.topic-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('.topic-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            const category = pill.getAttribute('data-category');
            document.querySelectorAll('.discover-card').forEach(card => {
                const cardCat = card.getAttribute('data-category');
                if (category === 'all' || !category || cardCat === category) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    // Demo Discovery Cards Click Handlers
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.discover-card, .prompt-chip');
        if (card && !isProcessing) {
            const promptText = card.getAttribute('data-prompt');
            if (promptText) {
                if (textInput) textInput.value = promptText;
                currentSTTDurationMs = null;
                handleUserQuery(promptText, false);
                if (textInput) textInput.value = '';
            }
        }
    });

    // Theme Toggle Handler
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            themeToggleBtn.innerHTML = newTheme === 'dark' ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
        });
    }

    // TTS Toggle Handler
    if (ttsToggleBtn) {
        ttsToggleBtn.addEventListener('click', () => {
            const isEnabled = speech.toggleTTS();
            ttsToggleBtn.innerHTML = isEnabled ? '<i class="fa-solid fa-volume-high"></i>' : '<i class="fa-solid fa-volume-xmark"></i>';
            ttsToggleBtn.style.opacity = isEnabled ? '1' : '0.5';
        });
    }

    // Main REST API Chat Handler
    async function handleUserQuery(text, isVoiceInput) {
        if (isProcessing && !speech.isListening) return;

        // Hide Welcome Card on first message
        if (welcomeCard) {
            welcomeCard.style.display = 'none';
        }

        // 1. Append User Message Bubble
        appendUserMessage(text);
        
        // Push user turn to conversation history
        sessionState.conversationHistory.push({ role: 'user', content: text });
        
        // 2. Set PROCESSING State & Disable Controls
        setSystemState('PROCESSING');
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    text: text,
                    conversation_history: sessionState.conversationHistory
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Update session state
                sessionState.totalMessages += 1;
                if (isVoiceInput) sessionState.voiceInputsCount += 1;
                
                const intentTag = data.intent;
                sessionState.intentsCount[intentTag] = (sessionState.intentsCount[intentTag] || 0) + 1;
                sessionState.confidenceScores.push(data.confidence_pct);
                
                // Push assistant turn to conversation history
                sessionState.conversationHistory.push({ role: 'assistant', content: data.response });
                
                // Update Analytics Side/Top Drawer
                updateSessionStatsUI();
                updateDrawerAnalysisUI(data, isVoiceInput, currentSTTDurationMs);

                // Append Assistant Bubble
                appendBotMessage(data, isVoiceInput, currentSTTDurationMs);

                // Scroll to latest message
                scrollToBottom();

                // Speech Synthesis Output
                if (speech.ttsEnabled) {
                    speech.speak(data.response);
                } else {
                    setSystemState('IDLE');
                }

            } else {
                appendErrorMessage(data.error || "Failed to process request.");
                setSystemState('IDLE');
            }
        } catch (err) {
            console.error("API Fetch Error:", err);
            appendErrorMessage("Could not connect to VocaSense backend server.");
            setSystemState('IDLE');
        }
    }

    // Append User Bubble
    function appendUserMessage(text) {
        const userDiv = document.createElement('div');
        userDiv.className = 'chat-bubble user-bubble';
        userDiv.innerHTML = `
            <div class="bubble-content">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        chatMessages.appendChild(userDiv);
        scrollToBottom();
    }

    // Append Assistant Message Bubble with Expandable Timeline & Technical Details
    function appendBotMessage(data, isVoiceInput, sttDurationMs) {
        const confPct = data.confidence_pct;
        let confClass = 'high';
        if (confPct < 45) confClass = 'low';
        else if (confPct < 70) confClass = 'medium';

        const why = data.why_this_response || {};
        const isGrok = data.response_mode === "GROK_AI";
        const requestId = data.request_id || "VS-LOCAL";
        const ttsActive = speech.ttsEnabled;

        const mlTimeStr = data.ml_inference_ms !== undefined ? `${data.ml_inference_ms} ms` : "Not measured";
        const grokTimeStr = data.grok_api_ms ? `${data.grok_api_ms} ms` : (isGrok ? "Timing unavailable" : "Not used (Fallback active)");
        const totalTimeStr = data.total_backend_ms !== undefined ? `${data.total_backend_ms} ms` : "Timing unavailable";
        const sttTimeStr = isVoiceInput ? (sttDurationMs ? `${sttDurationMs} ms` : "Completed") : "Not used (Typed / Demo Prompt)";

        const botDiv = document.createElement('div');
        botDiv.className = 'chat-bubble bot-bubble';
        
        botDiv.innerHTML = `
            <div class="bubble-header">
                <span class="bot-avatar"><i class="fa-solid fa-robot"></i> ${isGrok ? 'Grok AI' : 'VocaSense AI'}</span>
                <span class="badge-mint-tag">${data.intent.toUpperCase()}</span>
                <span class="badge-conf ${confClass}">ML Conf: ${confPct}%</span>
            </div>
            
            <div class="bubble-content">
                <div class="response-text-body">${formatResponseText(data.response)}</div>
                
                <!-- Expandable Timeline Accordion -->
                <div class="bubble-accordion">
                    <div class="accordion-title" onclick="toggleAccordion(this)">
                        <i class="fa-solid fa-timeline"></i> Processing Timeline <i class="fa-solid fa-chevron-down" style="font-size: 0.7rem; margin-left: auto;"></i>
                    </div>
                    <div class="accordion-body">
                        <div style="display: flex; flex-direction: column; gap: 0.3rem;">
                            <div><i class="fa-solid fa-circle" style="font-size:0.45rem; vertical-align:middle; margin-right:4px; color:var(--violet-primary);"></i> <strong>Speech Recognition:</strong> ${sttTimeStr}</div>
                            <div><i class="fa-solid fa-circle" style="font-size:0.45rem; vertical-align:middle; margin-right:4px; color:var(--violet-primary);"></i> <strong>BiLSTM Intent Classification:</strong> Intent: ${data.intent.toUpperCase()} (${confPct}%) | Time: ${mlTimeStr}</div>
                            <div><i class="fa-solid fa-circle" style="font-size:0.45rem; vertical-align:middle; margin-right:4px; color:var(--violet-primary);"></i> <strong>Grok Generation:</strong> ${isGrok ? `Latency: ${grokTimeStr}` : 'Fallback generator active'}</div>
                            <div><i class="fa-solid fa-circle" style="font-size:0.45rem; vertical-align:middle; margin-right:4px; color:var(--violet-primary);"></i> <strong>Total Backend Execution:</strong> ${totalTimeStr} (Request ID: <code>${requestId}</code>)</div>
                            <div><i class="fa-solid fa-circle" style="font-size:0.45rem; vertical-align:middle; margin-right:4px; color:var(--violet-primary);"></i> <strong>Text-to-Speech:</strong> ${ttsActive ? 'Activated' : 'Not activated (Muted)'}</div>
                        </div>
                    </div>
                </div>

                <!-- Expandable Technical Verification Accordion -->
                <div class="bubble-accordion">
                    <div class="accordion-title" onclick="toggleAccordion(this)">
                        <i class="fa-solid fa-code"></i> Technical Details <i class="fa-solid fa-chevron-down" style="font-size: 0.7rem; margin-left: auto;"></i>
                    </div>
                    <div class="accordion-body">
                        <div style="display: grid; grid-template-columns: 140px 1fr; gap: 0.3rem 0.75rem; font-family: 'JetBrains Mono', monospace;">
                            <span style="color: var(--text-muted);">Request ID:</span> <code>${requestId}</code>
                            <span style="color: var(--text-muted);">Input Source:</span> <span>${isVoiceInput ? 'Voice Microphone' : 'Typed / Demo Prompt'}</span>
                            <span style="color: var(--text-muted);">ML Model:</span> <span>BiLSTM (Keras)</span>
                            <span style="color: var(--text-muted);">ML Latency:</span> <span>${mlTimeStr}</span>
                            <span style="color: var(--text-muted);">Grok Model:</span> <span>${why.grok_model_name || data.response_engine}</span>
                            <span style="color: var(--text-muted);">Grok Latency:</span> <span>${grokTimeStr}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        chatMessages.appendChild(botDiv);
        scrollToBottom();
    }

    function appendErrorMessage(msg) {
        const errDiv = document.createElement('div');
        errDiv.className = 'chat-bubble bot-bubble';
        errDiv.innerHTML = `
            <div class="bubble-header">
                <span class="bot-avatar"><i class="fa-solid fa-triangle-exclamation"></i> System Notice</span>
            </div>
            <div class="bubble-content" style="border-color: rgba(239, 68, 68, 0.4);">
                <p style="color: #ef4444;">${escapeHtml(msg)}</p>
            </div>
        `;
        chatMessages.appendChild(errDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        if (chatViewport) {
            chatViewport.scrollTop = chatViewport.scrollHeight;
        }
    }

    function formatResponseText(text) {
        let formatted = escapeHtml(text);
        // Code blocks
        formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // Inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Bold text
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        return formatted;
    }

    // Update Session Stats UI
    function updateSessionStatsUI() {
        if (statMessages) statMessages.textContent = sessionState.totalMessages;
        if (statVoiceInputs) statVoiceInputs.textContent = sessionState.voiceInputsCount;
        
        let topTag = '—';
        let maxCount = 0;
        for (const [tag, count] of Object.entries(sessionState.intentsCount)) {
            if (count > maxCount) {
                maxCount = count;
                topTag = tag.toUpperCase();
            }
        }
        if (statTopIntent) statTopIntent.textContent = topTag;
        
        if (sessionState.confidenceScores.length > 0) {
            const sum = sessionState.confidenceScores.reduce((a, b) => a + b, 0);
            const avg = (sum / sessionState.confidenceScores.length).toFixed(1);
            if (statAvgConf) statAvgConf.textContent = `${avg}%`;
        }
    }

    // Update Analytics Drawer Detail Values
    function updateDrawerAnalysisUI(data, isVoiceInput, sttDurationMs) {
        if (metaIntent) metaIntent.textContent = data.intent ? data.intent.toUpperCase() : '—';
        if (metaConf) metaConf.textContent = data.confidence_pct ? `${data.confidence_pct}%` : '—';
        if (metaGrok) metaGrok.textContent = data.response_mode === 'GROK_AI' ? 'Grok AI' : 'Fallback Engine';
        if (metaReqId) metaReqId.textContent = data.request_id || 'VS-LOCAL';
        
        if (tTimeSTT) tTimeSTT.textContent = isVoiceInput ? (sttDurationMs ? `${sttDurationMs} ms` : 'Completed') : 'Not used';
        if (tTimeML) tTimeML.textContent = data.ml_inference_ms !== undefined ? `${data.ml_inference_ms} ms` : '—';
        if (tTimeGrok) tTimeGrok.textContent = data.grok_api_ms ? `${data.grok_api_ms} ms` : (data.response_mode === 'GROK_AI' ? 'Timing unavailable' : 'Fallback active');
        if (tTimeTotal) tTimeTotal.textContent = data.total_backend_ms !== undefined ? `${data.total_backend_ms} ms` : '—';
    }

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;")
                  .replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;")
                  .replace(/"/g, "&quot;")
                  .replace(/'/g, "&#039;");
    }

    // Global Accordion Drawer Handler
    window.toggleAccordion = function(el) {
        const body = el.nextElementSibling;
        if (!body) return;
        const isOpen = body.style.display === 'block';
        body.style.display = isOpen ? 'none' : 'block';
        const icon = el.querySelector('.fa-chevron-down, .fa-chevron-up');
        if (icon) {
            icon.classList.toggle('fa-chevron-down', isOpen);
            icon.classList.toggle('fa-chevron-up', !isOpen);
        }
    };
});
