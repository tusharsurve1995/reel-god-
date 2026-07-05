/**
 * REEL GOD Dashboard — JavaScript Controller
 * ===========================================
 * Manages AJAX actions for idea approval, rules registry, voice chat with TTS,
 * Instagram credential links, direct reel posting, and handles beautiful UI micro-animations.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Only execute if on the dashboard page to avoid errors on the login page
    if (!document.querySelector('.dashboard-container')) {
        return;
    }

    const socket = io();
    const consoleBody = document.getElementById('console-body');
    const rulesList = document.getElementById('rules-list');
    
    // Voice elements
    const btnVoiceToggle = document.getElementById('btn-voice-toggle');
    const btnVoiceStop = document.getElementById('btn-voice-stop');
    const btnVoiceSend = document.getElementById('btn-voice-send');
    const voiceChatInput = document.getElementById('voice-chat-input');
    const voiceChatHistory = document.getElementById('voice-chat-history');
    const audioEqualizer = document.getElementById('audio-equalizer');
    
    // Rules elements
    const btnAddRule = document.getElementById('btn-add-rule');
    const ruleInput = document.getElementById('rule-input');

    // Instagram settings elements
    const igPanel = document.getElementById('instagram-settings-panel');
    const igStatusInfo = document.getElementById('ig-status-info');
    const btnSaveIg = document.getElementById('btn-save-ig');
    const igUsernameInput = document.getElementById('ig-username-input');
    const igPasswordInput = document.getElementById('ig-password-input');

    let voiceEnabled = true;

    // Speech synthesis function with dynamic Equalizer visualizer
    function speak(text) {
        if (!voiceEnabled || !('speechSynthesis' in window)) return;
        
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Find suitable English voice
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            (voice.name.includes('Google') || voice.name.includes('Natural') || voice.name.includes('Microsoft')) && voice.lang.startsWith('en')
        ) || voices.find(voice => 
            voice.lang.startsWith('en')
        );
        
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        utterance.pitch = 0.95; 
        utterance.rate = 1.05;

        // Equalizer animations
        utterance.onstart = () => {
            if (audioEqualizer) audioEqualizer.classList.add('speaking');
        };
        utterance.onend = utterance.onerror = () => {
            if (audioEqualizer) audioEqualizer.classList.remove('speaking');
        };

        window.speechSynthesis.speak(utterance);
    }

    // Toggle Voice Mode
    if (btnVoiceToggle) {
        btnVoiceToggle.addEventListener('click', () => {
            voiceEnabled = !voiceEnabled;
            if (voiceEnabled) {
                btnVoiceToggle.innerHTML = '🔊 Voice: ENABLED';
                btnVoiceToggle.className = 'btn btn-approve';
                speak("Voice systems active.");
            } else {
                btnVoiceToggle.innerHTML = '🔇 Voice: MUTED';
                btnVoiceToggle.className = 'btn btn-reject';
                window.speechSynthesis.cancel();
                if (audioEqualizer) audioEqualizer.classList.remove('speaking');
            }
        });
    }

    if (btnVoiceStop) {
        btnVoiceStop.addEventListener('click', () => {
            window.speechSynthesis.cancel();
            if (audioEqualizer) audioEqualizer.classList.remove('speaking');
        });
    }

    // ── GEMINI LIVE REAL-TIME VOICE TALK (BIDIRECTIONAL STREAM) ────────────
    const btnLiveTalk = document.getElementById('btn-live-talk');
    const liveTalkStatus = document.getElementById('live-talk-status');

    let liveSocket = null;
    let audioContext = null;
    let playbackContext = null;
    let inputSource = null;
    let processorNode = null;
    let activeSources = [];
    let nextPlayTime = 0;
    let isLiveActive = false;

    // Convert Float32 audio to 16-bit signed PCM
    function floatTo16BitPCM(floatBuffer) {
        const buffer = new ArrayBuffer(floatBuffer.length * 2);
        const view = new DataView(buffer);
        let offset = 0;
        for (let i = 0; i < floatBuffer.length; i++, offset += 2) {
            let s = Math.max(-1, Math.min(1, floatBuffer[i]));
            // 16-bit signed PCM
            let val = s < 0 ? s * 0x8000 : s * 0x7FFF;
            view.setInt16(offset, val, true); // true = little-endian
        }
        return new Uint8Array(buffer);
    }

    // Convert Uint8Array to Base64
    function arrayBufferToBase64(uint8Array) {
        let binary = '';
        const len = uint8Array.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(uint8Array[i]);
        }
        return window.btoa(binary);
    }

    // Play PCM 24kHz Base64 chunk
    function playPCMChunk(base64Data) {
        if (!playbackContext) return;
        
        try {
            const binaryString = window.atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            const dataView = new DataView(bytes.buffer);
            const floatBuffer = new Float32Array(len / 2);
            for (let i = 0; i < floatBuffer.length; i++) {
                const sample = dataView.getInt16(i * 2, true); // little-endian
                floatBuffer[i] = sample / 32768.0;
            }
            
            const audioBuffer = playbackContext.createBuffer(1, floatBuffer.length, 24000);
            audioBuffer.getChannelData(0).set(floatBuffer);
            
            const source = playbackContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(playbackContext.destination);
            
            // Keep track of active nodes for interruption
            activeSources.push(source);
            source.onended = () => {
                const idx = activeSources.indexOf(source);
                if (idx !== -1) activeSources.splice(idx, 1);
                if (activeSources.length === 0 && audioEqualizer) {
                    audioEqualizer.classList.remove('speaking');
                }
            };
            
            const currentTime = playbackContext.currentTime;
            if (nextPlayTime < currentTime) {
                nextPlayTime = currentTime;
            }
            
            if (audioEqualizer) audioEqualizer.classList.add('speaking');
            source.start(nextPlayTime);
            nextPlayTime += audioBuffer.duration;
            
        } catch (e) {
            console.error("Failed to play audio chunk:", e);
        }
    }

    // Stop playback queue (interruption)
    function stopPlaybackQueue() {
        activeSources.forEach(src => {
            try { src.stop(); } catch (e) {}
        });
        activeSources = [];
        nextPlayTime = 0;
        if (audioEqualizer) audioEqualizer.classList.remove('speaking');
    }

    async function startLiveSession() {
        let configData;
        try {
            const res = await fetch('/api/gemini-live/config');
            configData = await res.json();
        } catch (e) {
            alert("Failed to fetch live settings config.");
            return;
        }

        if (!configData.api_key) {
            alert("Please link your Gemini API Key first.");
            return;
        }

        // Initialize Audio Contexts
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        playbackContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });

        // Connect WebSocket
        const wssUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=${configData.api_key}`;
        liveSocket = new WebSocket(wssUrl);

        liveSocket.onopen = () => {
            console.log("Gemini Live WebSocket connected!");
            
            // Send Setup Message
            const setupMsg = {
                setup: {
                    model: configData.model,
                    generationConfig: {
                        responseModalities: ["AUDIO"],
                        speechConfig: {
                            voiceConfig: {
                                prebuiltVoiceConfig: {
                                    voiceName: "Aoede" // beautiful female voice
                                }
                            }
                        }
                    },
                    systemInstruction: {
                        parts: [
                            { text: configData.system_instruction + "\nYou are in Gemini Live voice mode. Speak briefly, concisely, and conversationally. Do not speak in long paragraphs. Be a conversational advisor." }
                        ]
                    }
                }
            };
            liveSocket.send(JSON.stringify(setupMsg));
            
            // Activate mic recording
            startMicRecording();
            
            isLiveActive = true;
            btnLiveTalk.innerHTML = "🛑 Stop Gemini Live (Active)";
            btnLiveTalk.style.background = "linear-gradient(135deg, #ff3366, #990000)";
            btnLiveTalk.style.boxShadow = "0 0 20px rgba(255, 51, 102, 0.4)";
            if (liveTalkStatus) liveTalkStatus.style.display = "flex";
            
            appendVoiceMessage("system", "Gemini Live session connected. Speak freely!");
        };

        liveSocket.onmessage = async (event) => {
            let message;
            if (event.data instanceof Blob) {
                const text = await event.data.text();
                message = JSON.parse(text);
            } else {
                message = JSON.parse(event.data);
            }

            if (message.serverContent) {
                if (message.serverContent.modelTurn) {
                    const parts = message.serverContent.modelTurn.parts || [];
                    for (const part of parts) {
                        if (part.text) {
                            appendVoiceMessage("model", part.text);
                        }
                        if (part.inlineData && part.inlineData.mimeType.startsWith("audio/pcm")) {
                            playPCMChunk(part.inlineData.data);
                        }
                    }
                }
                
                if (message.serverContent.interrupted) {
                    stopPlaybackQueue();
                }
            }
        };

        liveSocket.onclose = () => {
            console.log("Gemini Live WebSocket closed.");
            cleanupLiveTalk();
        };

        liveSocket.onerror = (err) => {
            console.error("WebSocket error:", err);
            cleanupLiveTalk();
        };
    }

    async function startMicRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            inputSource = audioContext.createMediaStreamSource(stream);
            
            // 4096 is a good chunk size for 16kHz
            processorNode = audioContext.createScriptProcessor(4096, 1, 1);
            
            processorNode.onaudioprocess = (e) => {
                if (!liveSocket || liveSocket.readyState !== WebSocket.OPEN) return;
                
                const inputData = e.inputBuffer.getChannelData(0);
                const pcmData = floatTo16BitPCM(inputData);
                const base64Audio = arrayBufferToBase64(pcmData);
                
                const audioInputMsg = {
                    realtimeInput: {
                        mediaChunks: [
                            {
                                mimeType: "audio/pcm",
                                data: base64Audio
                            }
                        ]
                    }
                };
                liveSocket.send(JSON.stringify(audioInputMsg));
            };
            
            inputSource.connect(processorNode);
            processorNode.connect(audioContext.destination);
            
        } catch (e) {
            console.error("Microphone capture failed:", e);
            alert("Microphone permission denied or unavailable.");
            cleanupLiveTalk();
        }
    }

    function cleanupLiveTalk() {
        isLiveActive = false;
        btnLiveTalk.innerHTML = "🎙️ Start Gemini Live (Real-time Voice)";
        btnLiveTalk.style.background = "linear-gradient(135deg, #00f0ff, #7000ff)";
        btnLiveTalk.style.boxShadow = "0 0 15px rgba(0, 240, 255, 0.2)";
        if (liveTalkStatus) liveTalkStatus.style.display = "none";

        stopPlaybackQueue();

        if (processorNode) {
            try { processorNode.disconnect(); } catch (e) {}
            processorNode = null;
        }
        if (inputSource) {
            try {
                inputSource.mediaStream.getTracks().forEach(track => track.stop());
            } catch (e) {}
            inputSource = null;
        }
        if (audioContext) {
            try { audioContext.close(); } catch (e) {}
            audioContext = null;
        }
        if (playbackContext) {
            try { playbackContext.close(); } catch (e) {}
            playbackContext = null;
        }
        if (liveSocket) {
            try { liveSocket.close(); } catch (e) {}
            liveSocket = null;
        }
    }

    function appendVoiceMessage(sender, text) {
        if (!voiceChatHistory) return;
        
        const lastMsg = voiceChatHistory.lastElementChild;
        const senderLabel = sender === "user" ? "Commander" : (sender === "model" ? "REEL GOD" : "SYSTEM");
        const color = sender === "user" ? "white" : (sender === "model" ? "var(--accent-cyan)" : "#ff3366");
        
        if (lastMsg && lastMsg.getAttribute("data-sender") === sender) {
            const textSpan = lastMsg.querySelector(".msg-text");
            if (textSpan) {
                textSpan.innerText += " " + text;
            }
        } else {
            const div = document.createElement("div");
            div.setAttribute("data-sender", sender);
            div.style.color = color;
            div.innerHTML = `<span style="font-weight: bold;">${senderLabel}:</span> <span class="msg-text">${text}</span>`;
            voiceChatHistory.appendChild(div);
        }
        voiceChatHistory.scrollTop = voiceChatHistory.scrollHeight;
    }

    if (btnLiveTalk) {
        btnLiveTalk.addEventListener('click', () => {
            if (isLiveActive) {
                cleanupLiveTalk();
            } else {
                window.speechSynthesis.cancel();
                startLiveSession();
            }
        });
    }

    // Welcome Briefing
    setTimeout(() => {
        speak("System online, Commander. Welcome back.");
    }, 1200);

    // Console printer
    function logToConsole(message, type = 'system') {
        if (!consoleBody) return;
        const line = document.createElement('div');
        line.classList.add('log-line', type);
        
        const timestamp = new Date().toLocaleTimeString();
        line.innerHTML = `<span class="log-time" style="color: rgba(255,255,255,0.25)">[${timestamp}]</span> ${message}`;
        
        consoleBody.appendChild(line);
        consoleBody.scrollTop = consoleBody.scrollHeight;
    }

    // ── INSTAGRAM SETTINGS DYNAMIC FLOW ────────────────────────────────

    window.toggleInstagramSettings = function() {
        if (!igPanel) return;
        if (igPanel.style.display === 'none') {
            igPanel.style.display = 'flex';
            loadInstagramStatus();
        } else {
            // Smooth slide-up transition
            igPanel.style.animation = 'slideUp 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)';
            setTimeout(() => {
                igPanel.style.display = 'none';
                igPanel.style.animation = ''; // Reset
            }, 280);
        }
    };

    function loadInstagramStatus() {
        if (!igStatusInfo) return;
        igStatusInfo.innerHTML = '<span style="color: var(--accent-cyan);">Querying Instagram session profile...</span>';
        fetch('/api/instagram/status')
        .then(res => {
            if (!res.ok) throw new Error("HTTP error " + res.status);
            return res.json();
        })
        .then(data => {
            if (data.configured) {
                igStatusInfo.innerHTML = `🟢 Linked Account: <strong style="color: #fff;">@${data.username}</strong> ${data.session_cached ? '(Session cached)' : '(Requires re-auth)'}`;
                if (igUsernameInput) igUsernameInput.value = data.username;
            } else {
                igStatusInfo.innerHTML = '🔴 Instagram Account disconnected. Enter credentials to link.';
            }
        })
        .catch(err => {
            igStatusInfo.innerHTML = '🔴 Instagram Account disconnected. Enter credentials to link.';
        });
    }

    if (btnSaveIg) {
        btnSaveIg.addEventListener('click', () => {
            const username = igUsernameInput ? igUsernameInput.value.trim() : '';
            const password = igPasswordInput ? igPasswordInput.value.trim() : '';
            
            if (!username || !password) {
                alert("Username and password are required.");
                return;
            }

            btnSaveIg.disabled = true;
            btnSaveIg.innerHTML = '🔗 Authenticating...';
            if (igStatusInfo) {
                igStatusInfo.innerHTML = '<span style="color: var(--accent-purple); animation: blink 1.2s infinite;">Testing authentication with Instagram servers...</span>';
            }
            
            fetch('/api/instagram/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, password: password })
            })
            .then(res => res.json())
            .then(data => {
                btnSaveIg.disabled = false;
                btnSaveIg.innerHTML = 'Link Profile';
                if (data.success) {
                    if (igPasswordInput) igPasswordInput.value = '';
                    logToConsole(`Instagram connected successfully: @${username}`, 'success');
                    speak(`Instagram connected successfully. Account control verified.`);
                    loadInstagramStatus();
                } else {
                    if (igStatusInfo) igStatusInfo.innerHTML = `🔴 Link Failed: ${data.error}`;
                    speak("Instagram connection failed. Check credentials.");
                }
            })
            .catch(err => {
                btnSaveIg.disabled = false;
                btnSaveIg.innerHTML = 'Link Profile';
                if (igStatusInfo) igStatusInfo.innerHTML = `🔴 Link Failed: ${err.message}`;
            });
        });
    }

    // ── DEPLOY TO INSTAGRAM DIRECT PUBLISHING ─────────────────────────

    window.deployToInstagram = function(postId) {
        logToConsole(`Starting deployment of Reel #${postId} to Instagram...`, 'system');
        speak("Deploying reel compilation to Instagram. Initiating private API upload.");
        
        const card = document.getElementById(`post-card-${postId}`);
        const deployBtn = card ? card.querySelector('.btn-deploy') : null;
        
        if (deployBtn) {
            deployBtn.disabled = true;
            deployBtn.innerHTML = '📤 Uploading Reel...';
            deployBtn.style.background = 'var(--accent-purple)';
            deployBtn.style.boxShadow = '0 0 15px var(--accent-purple)';
        }

        fetch('/api/instagram/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                logToConsole(`Upload job initiated in background for Reel #${postId}.`, 'system');
            } else {
                logToConsole(`Upload failed to start: ${data.error}`, 'error');
                if (deployBtn) {
                    deployBtn.disabled = false;
                    deployBtn.innerHTML = '🚀 Deploy to Instagram';
                    deployBtn.style.background = '';
                    deployBtn.style.boxShadow = '';
                }
            }
        });
    };

    // Socket.IO Listeners
    socket.on('connect', () => {
        logToConsole('Connection to REEL GOD established.', 'success');
    });

    socket.on('disconnect', () => {
        logToConsole('Lost connection to agent server.', 'error');
    });

    socket.on('log_update', (data) => {
        let type = 'system';
        const msg = data.log;
        if (msg.includes('✓') || msg.includes('SUCCESS') || msg.includes('compiled') || msg.includes('published')) type = 'success';
        if (msg.includes('✗') || msg.includes('failed') || msg.includes('Error')) type = 'error';
        if (msg.includes('dim') || msg.includes('Resized')) type = 'dim';
        
        logToConsole(msg, type);
    });

    // Receive Reel Publish Updates
    socket.on('publish_status', (data) => {
        const postId = data.post_id;
        const card = document.getElementById(`post-card-${postId}`);
        const deployBtn = card ? card.querySelector('.btn-deploy') : null;
        
        if (data.status === 'started') {
            if (deployBtn) {
                deployBtn.disabled = true;
                deployBtn.innerHTML = '📤 Uploading Reel...';
            }
        } else if (data.status === 'completed') {
            logToConsole(`>>> Reel #${postId} published successfully! Media ID: ${data.instagram_id}`, 'success');
            speak("Success. Reel successfully posted to your Instagram profile. Analytics syncing enabled.");
            if (card) {
                const actionContainer = card.querySelector('.post-deploy-action');
                if (actionContainer) {
                    actionContainer.style.transition = 'all 0.5s ease';
                    actionContainer.innerHTML = `
                        <span class="style-badge" style="background: rgba(57, 255, 20, 0.15); border-color: var(--accent-green); color: #9bff8c; text-transform: none; font-size: 0.7rem; width: 100%; text-align: center; padding: 0.4rem; animation: highlightGreen 1s ease;">
                            🚀 Posted to IG ID: ${data.instagram_id}
                        </span>
                    `;
                }
            }
        } else if (data.status === 'failed') {
            logToConsole(`>>> Reel #${postId} publish failed: ${data.error}`, 'error');
            speak(`Error. Instagram Reel upload failed: ${data.error}`);
            if (deployBtn) {
                deployBtn.disabled = false;
                deployBtn.innerHTML = '🚀 Deploy to Instagram';
                deployBtn.style.background = '';
                deployBtn.style.boxShadow = '';
            }
        }
    });

    // Receive Reel Generation Status
    socket.on('generation_status', (data) => {
        const ideaId = data.idea_id;
        const card = document.getElementById(`idea-card-${ideaId}`);
        
        if (data.status === 'started') {
            logToConsole(`>>> Starting Reel compilation for Idea #${ideaId}...`, 'system');
            speak("Beginning video generation. Constructing keyframes, generating layers, and mixing audio tracks.");
            if (card) {
                card.style.opacity = '0.7';
                const genBtn = card.querySelector('.btn-generate');
                if (genBtn) {
                    genBtn.disabled = true;
                    genBtn.innerHTML = '⚡ Compiling...';
                }
            }
        } else if (data.status === 'completed') {
            logToConsole(`>>> Compilation complete for Idea #${ideaId}! Saved as: ${data.filename}`, 'success');
            speak(`Success. Compilation finished for idea number ${ideaId}. Audio-mixed reel saved successfully.`);
            if (card) {
                card.style.transition = 'all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1)';
                card.style.transform = 'scale(0.8) translateY(-20px)';
                card.style.opacity = '0';
                setTimeout(() => {
                    card.remove();
                    window.location.reload();
                }, 500);
            }
        } else if (data.status === 'failed') {
            logToConsole(`>>> Compilation failed for Idea #${ideaId}: ${data.error}`, 'error');
            speak(`Error. Reel compilation failed due to: ${data.error}`);
            if (card) {
                card.style.opacity = '1';
                const genBtn = card.querySelector('.btn-generate');
                if (genBtn) {
                    genBtn.disabled = false;
                    genBtn.innerHTML = '🎬 Compile Reel';
                }
            }
        }
    });

    // Approve Idea
    window.approveIdea = function(ideaId) {
        logToConsole(`Approving Idea #${ideaId}...`, 'system');
        fetch(`/api/idea/${ideaId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                logToConsole(`Idea #${ideaId} approved by Commander.`, 'success');
                speak("Content idea approved. Ready to compile.");
                const card = document.getElementById(`idea-card-${ideaId}`);
                if (card) {
                    const actionsDiv = card.querySelector('.idea-actions');
                    if (actionsDiv) {
                        actionsDiv.innerHTML = `
                            <button class="btn btn-generate" onclick="generateReel(${ideaId})">
                                🎬 Compile Reel
                            </button>
                        `;
                    }
                }
            } else {
                logToConsole(`Failed to approve idea: ${data.error}`, 'error');
            }
        });
    };

    // Reject Idea
    window.rejectIdea = function(ideaId) {
        const reason = prompt("Enter reason for rejection:");
        if (reason === null) return;
        
        logToConsole(`Rejecting Idea #${ideaId}...`, 'system');
        fetch(`/api/idea/${ideaId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                logToConsole(`Idea #${ideaId} rejected. Reason: ${reason}`, 'dim');
                speak(`Content idea rejected. Reason noted.`);
                const card = document.getElementById(`idea-card-${ideaId}`);
                if (card) {
                    card.style.transition = 'all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)';
                    card.style.transform = 'translateY(30px) scale(0.9)';
                    card.style.opacity = '0';
                    setTimeout(() => card.remove(), 400);
                }
            } else {
                logToConsole(`Failed to reject idea: ${data.error}`, 'error');
            }
        });
    };

    // Compile Reel
    window.generateReel = function(ideaId) {
        fetch(`/api/idea/${ideaId}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                logToConsole(`Compilation requested for Idea #${ideaId}. Starting background process...`, 'system');
            } else {
                logToConsole(`Failed to trigger generation: ${data.error}`, 'error');
            }
        });
    };

    // ── RULES MANAGEMENT ───────────────────────────────────────────────

    if (btnAddRule) {
        btnAddRule.addEventListener('click', () => {
            const ruleText = ruleInput ? ruleInput.value.trim() : '';
            if (!ruleText) return;
            
            logToConsole(`Teaching rule to agent: "${ruleText}"...`, 'system');
            fetch('/api/rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rule: ruleText })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (ruleInput) ruleInput.value = '';
                    logToConsole(`Rule successfully stored in agent memory core.`, 'success');
                    speak("Rule received and stored in database. I have integrated this preference into my system instructions.");
                    
                    if (rulesList) {
                        const dateStr = new Date().toISOString().split('T')[0];
                        const ruleItem = document.createElement('div');
                        ruleItem.id = `rule-item-${data.id}`;
                        ruleItem.className = 'schedule-item rule-card-item';
                        ruleItem.style.cssText = 'align-items: flex-start; flex-direction: column; gap: 0.4rem; padding: 0.75rem; opacity: 0; transform: translateY(-10px); transition: all 0.3s ease;';
                        ruleItem.innerHTML = `
                            <div style="font-size: 0.9rem; font-weight: 500; color: white; word-break: break-word;">${ruleText}</div>
                            <div style="display: flex; justify-content: space-between; width: 100%; align-items: center; margin-top: 0.25rem;">
                                <span style="font-size: 0.7rem; color: var(--text-secondary);">Taught: ${dateStr}</span>
                                <button class="btn btn-reject" onclick="deleteRule(${data.id})" style="padding: 0.2rem 0.6rem; font-size: 0.75rem; border-radius: 4px;">Delete</button>
                            </div>
                        `;
                        rulesList.prepend(ruleItem);
                        setTimeout(() => {
                            ruleItem.style.opacity = '1';
                            ruleItem.style.transform = 'translateY(0)';
                        }, 50);
                    }
                } else {
                    logToConsole(`Failed to add rule: ${data.error}`, 'error');
                }
            });
        });
    }

    // Delete Rule
    window.deleteRule = function(ruleId) {
        logToConsole(`Removing rule ID #${ruleId} from memory...`, 'system');
        fetch(`/api/rule/${ruleId}/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                logToConsole(`Rule ID #${ruleId} removed.`, 'dim');
                speak("Preference removed from system instructions.");
                const item = document.getElementById(`rule-item-${ruleId}`);
                if (item) {
                    item.style.transition = 'all 0.3s ease';
                    item.style.opacity = '0';
                    item.style.transform = 'translateY(10px)';
                    setTimeout(() => item.remove(), 300);
                }
            } else {
                logToConsole(`Failed to delete rule: ${data.error}`, 'error');
            }
        });
    };

    // ── VOICE CHAT COMMINUCATION ───────────────────────────────────────

    function sendVoiceChatMessage() {
        if (!voiceChatInput) return;
        const messageText = voiceChatInput.value.trim();
        if (!messageText) return;
        
        voiceChatInput.value = '';
        
        // Add to history
        if (voiceChatHistory) {
            const userDiv = document.createElement('div');
            userDiv.style.cssText = 'color: #fff; text-align: right; background: rgba(255,255,255,0.05); padding: 0.5rem 0.75rem; border-radius: 8px; align-self: flex-end; max-width: 80%; word-break: break-word; animation: slideIn 0.3s ease;';
            userDiv.innerHTML = `COMMANDER: "${messageText}"`;
            voiceChatHistory.appendChild(userDiv);
            voiceChatHistory.scrollTop = voiceChatHistory.scrollHeight;
        }
        
        speak("Processing input...");
        
        fetch('/api/voice-chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: messageText })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const responseText = data.response;
                
                if (voiceChatHistory) {
                    const agentDiv = document.createElement('div');
                    agentDiv.style.cssText = 'color: var(--accent-cyan); background: rgba(0,240,255,0.04); padding: 0.5rem 0.75rem; border-radius: 8px; align-self: flex-start; max-width: 80%; word-break: break-word; animation: slideIn 0.3s ease;';
                    agentDiv.innerHTML = `REEL GOD: "${responseText}"`;
                    voiceChatHistory.appendChild(agentDiv);
                    voiceChatHistory.scrollTop = voiceChatHistory.scrollHeight;
                }
                
                speak(responseText);
            } else {
                if (voiceChatHistory) {
                    const errorDiv = document.createElement('div');
                    errorDiv.style.color = 'var(--accent-red)';
                    errorDiv.style.fontSize = '0.85rem';
                    errorDiv.innerHTML = `ERROR: ${data.error}`;
                    voiceChatHistory.appendChild(errorDiv);
                }
            }
        });
    }

    if (btnVoiceSend) btnVoiceSend.addEventListener('click', sendVoiceChatMessage);
    if (voiceChatInput) {
        voiceChatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendVoiceChatMessage();
        });
    }

    // ── VIDEO CO-PILOT FUNCTIONS ──────────────────────────────────────
    
    const copilotUploadArea = document.getElementById('copilot-upload-area');
    const copilotFileInput = document.getElementById('copilot-file-input');
    const copilotAnalysisPanel = document.getElementById('copilot-analysis-panel');
    const copilotKeyframesGrid = document.getElementById('copilot-keyframes-grid');
    const copilotInstructionInput = document.getElementById('copilot-instruction-input');
    const btnCopilotAnalyze = document.getElementById('btn-copilot-analyze');
    const copilotScriptPanel = document.getElementById('copilot-script-panel');
    
    const copilotScriptTitle = document.getElementById('copilot-script-title');
    const copilotScriptTheme = document.getElementById('copilot-script-theme');
    const copilotScriptMusic = document.getElementById('copilot-script-music');
    const copilotScriptSubtitles = document.getElementById('copilot-script-subtitles');
    const copilotScriptCaption = document.getElementById('copilot-script-caption');
    const btnCopilotCompile = document.getElementById('btn-copilot-compile');

    let copilotUploadedFilepath = "";
    let copilotLatestAnalysis = null;

    if (copilotUploadArea) {
        copilotUploadArea.addEventListener('click', () => {
            copilotFileInput.click();
        });
    }

    window.handleVideoFileSelect = function(e) {
        const file = e.target.files[0];
        if (file) uploadVideoFile(file);
    };

    window.handleVideoDrop = function(e) {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'video/mp4') {
            uploadVideoFile(file);
        } else {
            alert("Please drop a valid .mp4 video file.");
        }
    };

    function uploadVideoFile(file) {
        logToConsole(`Uploading video file '${file.name}' to Co-Pilot...`, 'system');
        
        if (copilotUploadArea) {
            copilotUploadArea.innerHTML = `
                <span class="equalizer-bar speaking" style="margin: 0 auto 0.75rem;">
                    <span></span><span></span><span></span>
                </span>
                <span style="font-weight: 600; display: block;">Uploading & Slicing Keyframes...</span>
                <span style="font-size: 0.8rem; color: var(--text-secondary);">Processing locally, please wait.</span>
            `;
        }

        const formData = new FormData();
        formData.append('video', file);

        fetch('/api/co-pilot/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                copilotUploadedFilepath = data.filepath;
                logToConsole("Video uploaded successfully. Keyframes extracted.", 'success');
                speak("Video uploaded and keyframes extracted successfully.");
                
                if (copilotUploadArea) copilotUploadArea.style.display = 'none';
                if (copilotAnalysisPanel) copilotAnalysisPanel.style.display = 'flex';
                
                if (copilotKeyframesGrid) {
                    copilotKeyframesGrid.innerHTML = '';
                    data.keyframes.forEach(src => {
                        const img = document.createElement('img');
                        img.src = src;
                        img.style.cssText = 'width: 100%; aspect-ratio: 16/9; object-fit: cover; border-radius: 6px; border: 1px solid rgba(255,255,255,0.08);';
                        copilotKeyframesGrid.appendChild(img);
                    });
                }
            } else {
                alert(`Upload failed: ${data.error}`);
                resetCopilot();
            }
        })
        .catch(err => {
            alert(`Error: ${err}`);
            resetCopilot();
        });
    }

    if (btnCopilotAnalyze) {
        btnCopilotAnalyze.addEventListener('click', () => {
            const instructionText = copilotInstructionInput.value.trim();
            logToConsole("Co-Pilot: Initiating Gemini Multimodal Video Analysis...", 'system');
            
            btnCopilotAnalyze.disabled = true;
            btnCopilotAnalyze.innerHTML = "🔍 Running Visual Reasoning...";
            speak("Calling Gemini to analyze visual sequences.");

            fetch('/api/co-pilot/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filepath: copilotUploadedFilepath,
                    instruction: instructionText
                })
            })
            .then(res => res.json())
            .then(data => {
                btnCopilotAnalyze.disabled = false;
                btnCopilotAnalyze.innerHTML = "🔍 Analyze Video with Gemini";

                if (data.success) {
                    copilotLatestAnalysis = data.analysis;
                    logToConsole("Co-Pilot: Gemini returned structured editing plan.", 'success');
                    speak("Analysis complete. Gemini has suggested an editing plan.");
                    
                    if (copilotScriptPanel) copilotScriptPanel.style.display = 'flex';
                    
                    if (copilotScriptTitle) copilotScriptTitle.innerHTML = `🎬 Title: ${copilotLatestAnalysis.title}`;
                    if (copilotScriptTheme) copilotScriptTheme.innerHTML = `💡 Theme: ${copilotLatestAnalysis.theme} (Format: ${copilotLatestAnalysis.aspect_ratio})`;
                    if (copilotScriptMusic) copilotScriptMusic.innerHTML = `🎵 Music query: ${copilotLatestAnalysis.music_query}`;
                    if (copilotScriptCaption) copilotScriptCaption.innerHTML = `📝 Caption: ${copilotLatestAnalysis.caption}`;
                    
                    if (copilotScriptSubtitles) {
                        copilotScriptSubtitles.innerHTML = '';
                        copilotLatestAnalysis.narrative.forEach((sub, idx) => {
                            const subLine = document.createElement('div');
                            subLine.style.cssText = 'font-size: 0.85rem; padding: 0.4rem; background: rgba(255,255,255,0.03); border-radius: 4px; display: flex; justify-content: space-between;';
                            subLine.innerHTML = `
                                <span>Line ${idx+1}: <strong>"${sub.text}"</strong></span>
                                <span style="color: var(--accent-cyan);">${sub.duration}s</span>
                            `;
                            copilotScriptSubtitles.appendChild(subLine);
                        });
                    }
                } else {
                    alert(`Analysis failed: ${data.error}`);
                }
            })
            .catch(err => {
                btnCopilotAnalyze.disabled = false;
                btnCopilotAnalyze.innerHTML = "🔍 Analyze Video with Gemini";
                alert(`Error: ${err}`);
            });
        });
    }

    const copilotProgressContainer = document.getElementById('copilot-progress-container');
    const copilotProgressStage = document.getElementById('copilot-progress-stage');
    const copilotProgressPercent = document.getElementById('copilot-progress-percent');
    const copilotProgressBar = document.getElementById('copilot-progress-bar');

    if (btnCopilotCompile) {
        btnCopilotCompile.addEventListener('click', () => {
            if (!copilotUploadedFilepath || !copilotLatestAnalysis) return;

            logToConsole("Co-Pilot: Dispatching compilation thread...", 'system');
            
            // Show progress bar container, hide compile button
            if (copilotProgressContainer) copilotProgressContainer.style.display = 'flex';
            if (btnCopilotCompile) btnCopilotCompile.style.display = 'none';
            if (copilotProgressStage) copilotProgressStage.innerHTML = "Initializing synthesis...";
            if (copilotProgressPercent) copilotProgressPercent.innerHTML = "0%";
            if (copilotProgressBar) copilotProgressBar.style.width = "0%";

            speak("Synthesizing reel elements in the background.");

            fetch('/api/co-pilot/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filepath: copilotUploadedFilepath,
                    analysis: copilotLatestAnalysis
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    logToConsole("Co-Pilot: Synthesis background task started.", 'dim');
                } else {
                    if (copilotProgressContainer) copilotProgressContainer.style.display = 'none';
                    if (btnCopilotCompile) btnCopilotCompile.style.display = 'block';
                    alert(`Compilation failed: ${data.error}`);
                }
            })
            .catch(err => {
                if (copilotProgressContainer) copilotProgressContainer.style.display = 'none';
                if (btnCopilotCompile) btnCopilotCompile.style.display = 'block';
                alert(`Error: ${err}`);
            });
        });
    }

    window.resetCopilot = function() {
        copilotUploadedFilepath = "";
        copilotLatestAnalysis = null;
        if (copilotFileInput) copilotFileInput.value = '';
        
        if (copilotUploadArea) {
            copilotUploadArea.style.display = 'block';
            copilotUploadArea.innerHTML = `
                <span style="font-size: 2.5rem; display: block; margin-bottom: 0.75rem;">📁</span>
                <span style="font-weight: 600; display: block; margin-bottom: 0.25rem;">Drag & Drop Video File</span>
                <span style="font-size: 0.8rem; color: var(--text-secondary);">or click to select file (.mp4 format)</span>
            `;
        }
        if (copilotAnalysisPanel) copilotAnalysisPanel.style.display = 'none';
        if (copilotScriptPanel) copilotScriptPanel.style.display = 'none';
        if (copilotProgressContainer) copilotProgressContainer.style.display = 'none';
        if (btnCopilotCompile) btnCopilotCompile.style.display = 'block';
    };

    // Socket.IO event handler for Co-Pilot progress updates
    socket.on('copilot_progress', (data) => {
        if (copilotProgressStage) copilotProgressStage.innerHTML = data.stage;
        if (copilotProgressPercent) copilotProgressPercent.innerHTML = `${data.percent}%`;
        if (copilotProgressBar) copilotProgressBar.style.width = `${data.percent}%`;
        logToConsole(`Co-Pilot compile progress: ${data.percent}% - ${data.stage}`, 'dim');
    });

    socket.on('copilot_status', (data) => {
        if (data.status === 'completed') {
            if (copilotProgressPercent) copilotProgressPercent.innerHTML = "100%";
            if (copilotProgressBar) copilotProgressBar.style.width = "100%";
            if (copilotProgressStage) copilotProgressStage.innerHTML = "Production complete!";

            logToConsole(`Co-Pilot complete! Output name: ${data.filename}`, 'success');
            speak("Compilation complete! Your visual masterpiece has been added to the Reels Archive.");
            
            setTimeout(() => {
                resetCopilot();
                window.location.reload();
            }, 3000);
        } else if (data.status === 'failed') {
            logToConsole(`Co-Pilot compilation task failed: ${data.error}`, 'error');
            speak("Compilation failed. Please inspect the logs.");
            if (copilotProgressContainer) copilotProgressContainer.style.display = 'none';
            if (btnCopilotCompile) {
                btnCopilotCompile.style.display = 'block';
                btnCopilotCompile.disabled = false;
                btnCopilotCompile.innerHTML = "🎬 Compile Masterpiece";
            }
        }
    });

    // ═══════════════════════════════════════════════════════════════
    //  INSTAGRAM REEL CREATOR
    // ═══════════════════════════════════════════════════════════════
    let creatorTab = 'anime';
    let creatorUploadFilepath = null;

    const pretty = (s) => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const GENRE_LABEL = {
        auto: '🎯 Auto (mood match)', bollywood: '🇮🇳 Bollywood', hollywood: '🎞️ Hollywood',
        pop: '🎤 Pop', instrumental: '🎹 Instrumental', action: '💥 Action',
        romantic: '💗 Romantic', worldwide: '🌍 Worldwide'
    };

    function loadCreatorOptions() {
        fetch('/api/creator/options').then(r => r.json()).then(data => {
            const animeSel = document.getElementById('creator-anime');
            (data.animes || []).forEach(a => {
                const o = document.createElement('option');
                o.value = a.key; o.textContent = a.label; animeSel.appendChild(o);
            });
            const styleSel = document.getElementById('creator-style');
            (data.styles || []).forEach(s => {
                const o = document.createElement('option');
                o.value = s; o.textContent = pretty(s); styleSel.appendChild(o);
            });
            const genreSel = document.getElementById('creator-genre');
            (data.genres || []).forEach(g => {
                const o = document.createElement('option');
                o.value = g; o.textContent = GENRE_LABEL[g] || pretty(g); genreSel.appendChild(o);
            });
            const stockStatus = document.getElementById('creator-stock-status');
            const sources = data.stock_sources || [];
            if (stockStatus && sources.length === 0) {
                stockStatus.innerHTML = '⚠️ No stock source configured yet. Add a free ' +
                    '<b>PEXELS_API_KEY</b> or <b>PIXABAY_API_KEY</b> and restart to enable this. ' +
                    'Until then, use the <b>Upload</b> tab.';
            } else if (stockStatus && sources.length) {
                stockStatus.innerHTML = '✅ Sources ready: <b>' + sources.join(', ') + '</b>. ' +
                    'Type a directive below (e.g. "sunrise over mountains") or leave blank to match your Mood/Style.';
            }
        }).catch(e => logToConsole('Failed to load creator options: ' + e, 'error'));
    }
    loadCreatorOptions();

    window.toggleReelCreator = () => {
        const p = document.getElementById('reel-creator-panel');
        if (p) p.style.display = (p.style.display === 'none' || !p.style.display) ? 'flex' : 'none';
    };

    window.switchCreatorTab = (tab) => {
        creatorTab = tab;
        const anime = document.getElementById('creator-anime-source');
        const stock = document.getElementById('creator-stock-source');
        const upload = document.getElementById('creator-upload-source');
        const tA = document.getElementById('tab-anime');
        const tS = document.getElementById('tab-stock');
        const tU = document.getElementById('tab-upload');
        anime.style.display = 'none'; stock.style.display = 'none'; upload.style.display = 'none';
        tA.classList.remove('creator-tab-active');
        tS.classList.remove('creator-tab-active');
        tU.classList.remove('creator-tab-active');
        if (tab === 'anime') {
            anime.style.display = 'flex'; tA.classList.add('creator-tab-active');
        } else if (tab === 'stock') {
            stock.style.display = 'flex'; tS.classList.add('creator-tab-active');
        } else {
            upload.style.display = 'flex'; tU.classList.add('creator-tab-active');
        }
    };

    function uploadCreatorFile(file) {
        if (!file) return;
        const label = document.getElementById('creator-upload-label');
        label.textContent = `Uploading ${file.name}...`;
        const fd = new FormData();
        fd.append('media', file);
        fetch('/api/creator/upload', { method: 'POST', body: fd })
            .then(r => r.json()).then(data => {
                if (data.success) {
                    creatorUploadFilepath = data.filepath;
                    label.textContent = `✓ ${file.name} (${data.kind}) ready`;
                    logToConsole(`Uploaded ${data.kind}: ${file.name}`, 'success');
                } else {
                    label.textContent = 'Upload failed'; logToConsole('Upload failed: ' + data.error, 'error');
                }
            }).catch(e => { label.textContent = 'Upload failed'; logToConsole('Upload error: ' + e, 'error'); });
    }

    window.handleCreatorFileSelect = (ev) => { uploadCreatorFile(ev.target.files[0]); };
    window.handleCreatorDrop = (ev) => {
        ev.preventDefault();
        if (ev.dataTransfer.files && ev.dataTransfer.files[0]) uploadCreatorFile(ev.dataTransfer.files[0]);
    };

    window.runCreator = () => {
        const payload = {
            style: document.getElementById('creator-style').value,
            format: document.getElementById('creator-format').value,
            genre: document.getElementById('creator-genre').value,
            instruction: document.getElementById('creator-instruction').value,
        };
        let url;
        if (creatorTab === 'anime') {
            url = '/api/creator/anime';
            payload.anime = document.getElementById('creator-anime').value;
        } else if (creatorTab === 'stock') {
            url = '/api/creator/stock';
        } else {
            if (!creatorUploadFilepath) { alert('Please upload a photo or video first.'); return; }
            url = '/api/creator/compile-upload';
            payload.filepath = creatorUploadFilepath;
        }
        const btn = document.getElementById('btn-creator-create');
        btn.disabled = true; btn.innerHTML = '⏳ Creating...';
        document.getElementById('creator-progress-container').style.display = 'flex';
        fetch(url, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(r => r.json()).then(data => {
            if (!data.success) {
                logToConsole('Creator failed to start: ' + data.error, 'error');
                btn.disabled = false; btn.innerHTML = '✨ Create';
            } else {
                logToConsole('Reel Creator started: ' + data.message, 'system');
            }
        }).catch(e => { logToConsole('Creator error: ' + e, 'error'); btn.disabled = false; btn.innerHTML = '✨ Create'; });
    };

    socket.on('creator_progress', (data) => {
        const stage = document.getElementById('creator-progress-stage');
        const pct = document.getElementById('creator-progress-percent');
        const bar = document.getElementById('creator-progress-bar');
        if (stage) stage.innerHTML = data.stage;
        if (pct) pct.innerHTML = `${data.percent}%`;
        if (bar) bar.style.width = `${data.percent}%`;
    });

    socket.on('creator_status', (data) => {
        const btn = document.getElementById('btn-creator-create');
        if (data.status === 'completed') {
            logToConsole(`Reel Creator complete: ${data.filename}`, 'success');
            speak('Your ' + (data.format || 'reel') + ' is ready and added to the archive.');
            const stage = document.getElementById('creator-progress-stage');
            if (stage) stage.innerHTML = 'Done! Refreshing...';
            setTimeout(() => window.location.reload(), 2500);
        } else if (data.status === 'failed') {
            logToConsole('Reel Creator failed: ' + data.error, 'error');
            speak('Creation failed. Please check the logs.');
            if (btn) { btn.disabled = false; btn.innerHTML = '✨ Create'; }
        }
    });

    window.savePostPerformance = (postId) => {
        const card = document.getElementById(`post-card-${postId}`);
        const views = parseInt(card.querySelector('.metrics-views').value) || 0;
        const likes = parseInt(card.querySelector('.metrics-likes').value) || 0;
        const comments = parseInt(card.querySelector('.metrics-comments').value) || 0;
        const saves = parseInt(card.querySelector('.metrics-saves').value) || 0;
        const feedback = card.querySelector('.metrics-feedback').value || '';
        const isPosted = card.querySelector('.metrics-status').checked ? 1 : 0;
        
        fetch(`/api/post/${postId}/performance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ views, likes, comments, saves, feedback, is_posted: isPosted })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                alert("Story posting metrics saved! Memory updated.");
                window.location.reload();
            } else {
                alert("Failed to save: " + data.error);
            }
        })
        .catch(e => alert("Connection error: " + e));
    };
});
