/**
 * Speechee UI Application
 * Provided by Friday
 */

// ========================================
// STATE
// ========================================
const State = {
    currentFile: null,
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    recordingTimer: null,
    recordingSeconds: 0,
    lastResult: null
};

// ========================================
// DOM ELEMENTS
// ========================================
const DOM = {
    // Status
    statusBadge: document.getElementById('status-badge'),
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),
    
    // Upload
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),
    fileInfo: document.getElementById('file-info'),
    fileName: document.getElementById('file-name'),
    fileSize: document.getElementById('file-size'),
    
    // Recording
    recordBtn: document.getElementById('record-btn'),
    recordTimer: document.getElementById('record-timer'),
    recordStatus: document.getElementById('record-status'),
    waveform: document.getElementById('waveform'),
    
    // Settings
    modelSelect: document.getElementById('model-select'),
    languageSelect: document.getElementById('language-select'),
    durationSelect: document.getElementById('duration-select'),
    
    // Actions
    transcribeBtn: document.getElementById('transcribe-btn'),
    
    // Result
    resultArea: document.getElementById('result-area'),
    resultText: document.getElementById('result-text'),
    resultPlaceholder: document.getElementById('result-placeholder'),
    resultMeta: document.getElementById('result-meta'),
    
    // Sidebar
    statsEngine: document.getElementById('stats-engine'),
    statsModels: document.getElementById('stats-models'),
    statsDevices: document.getElementById('stats-devices'),
    modelsList: document.getElementById('models-list'),
    devicesList: document.getElementById('devices-list'),
    transcriptsList: document.getElementById('transcripts-list'),
    configDisplay: document.getElementById('config-display'),
    
    // Language Detection
    langInput: document.getElementById('lang-input'),
    langDetectBtn: document.getElementById('lang-detect-btn'),
    langResult: document.getElementById('lang-result'),
    
    // Loader
    loader: document.getElementById('loader'),
    loaderText: document.getElementById('loader-text'),
    
    // Toast
    toastContainer: document.getElementById('toast-container')
};

// ========================================
// UTILITY FUNCTIONS
// ========================================
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
}

function showLoader(text = 'Processing...') {
    DOM.loaderText.textContent = text;
    DOM.loader.classList.remove('hidden');
}

function hideLoader() {
    DOM.loader.classList.add('hidden');
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
        <span class="toast-message">${message}</span>
    `;
    DOM.toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ========================================
// TAB SWITCHING
// ========================================
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`panel-${tabName}`).classList.add('active');
}

// ========================================
// SYSTEM STATUS
// ========================================
async function loadSystemStatus() {
    try {
        const health = await SpeecheeAPI.getHealth();
        
        if (health.status === 'healthy') {
            DOM.statusDot.className = 'status-dot online';
            DOM.statusText.textContent = 'Online';
        } else {
            DOM.statusDot.className = 'status-dot degraded';
            DOM.statusText.textContent = 'Degraded';
        }
        
        DOM.statsEngine.textContent = health.engine_ready ? '✓ Ready' : '✗ Missing';
        DOM.statsEngine.className = health.engine_ready ? 'stat-value success' : 'stat-value error';
        DOM.statsModels.textContent = health.models_available;
        
    } catch (error) {
        DOM.statusDot.className = 'status-dot offline';
        DOM.statusText.textContent = 'Offline';
    }
}

// ========================================
// MODELS
// ========================================
async function loadModels() {
    try {
        const data = await SpeecheeAPI.getModels();
        
        // Update select dropdown
        DOM.modelSelect.innerHTML = '';
        data.models.filter(m => m.downloaded).forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = `${model.name} (${model.speed})`;
            if (model.name === data.default) option.selected = true;
            DOM.modelSelect.appendChild(option);
        });
        
        // Update sidebar list
        DOM.modelsList.innerHTML = '';
        data.models.forEach(model => {
            const div = document.createElement('div');
            div.className = 'model-item';
            div.innerHTML = `
                <div class="model-info">
                    <span class="model-name">${model.name}</span>
                    <span class="model-meta">${model.size_mb}MB • ${model.language}</span>
                </div>
                <span class="model-status ${model.downloaded ? 'ready' : 'missing'}">
                    ${model.downloaded ? '✓' : '✗'}
                </span>
            `;
            DOM.modelsList.appendChild(div);
        });
        
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

// ========================================
// DEVICES
// ========================================
async function loadDevices() {
    try {
        const data = await SpeecheeAPI.getDevices();
        
        DOM.statsDevices.textContent = data.total;
        
        DOM.devicesList.innerHTML = '';
        if (data.devices.length === 0) {
            DOM.devicesList.innerHTML = '<p class="empty-message">No devices found</p>';
            return;
        }
        
        data.devices.forEach(device => {
            const div = document.createElement('div');
            div.className = 'device-item';
            div.innerHTML = `
                <span class="device-icon">🎤</span>
                <span class="device-name">${device.name}</span>
                ${device.is_default ? '<span class="device-badge">DEFAULT</span>' : ''}
            `;
            DOM.devicesList.appendChild(div);
        });
        
    } catch (error) {
        console.error('Failed to load devices:', error);
    }
}

// ========================================
// CONFIG
// ========================================
async function loadConfig() {
    try {
        const data = await SpeecheeAPI.getConfig();
        
        DOM.configDisplay.innerHTML = `
            <div class="config-group">
                <h4>STT</h4>
                <div class="config-row">
                    <span>Model:</span>
                    <code>${data.config.stt?.model || '--'}</code>
                </div>
                <div class="config-row">
                    <span>Language:</span>
                    <code>${data.config.stt?.language || '--'}</code>
                </div>
            </div>
            <div class="config-group">
                <h4>Audio</h4>
                <div class="config-row">
                    <span>Sample Rate:</span>
                    <code>${data.config.audio?.sample_rate || '--'} Hz</code>
                </div>
                <div class="config-row">
                    <span>Duration:</span>
                    <code>${data.config.audio?.default_duration || '--'}s</code>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

// ========================================
// TRANSCRIPTS
// ========================================
async function loadTranscripts() {
    try {
        const data = await SpeecheeAPI.getTranscripts(10);
        
        DOM.transcriptsList.innerHTML = '';
        if (data.transcripts.length === 0) {
            DOM.transcriptsList.innerHTML = '<p class="empty-message">No transcripts saved</p>';
            return;
        }
        
        data.transcripts.forEach(t => {
            const div = document.createElement('div');
            div.className = 'transcript-item';
            div.innerHTML = `
                <div class="transcript-info">
                    <span class="transcript-name">${t.filename}</span>
                    <span class="transcript-size">${formatBytes(t.size_bytes)}</span>
                </div>
                <div class="transcript-actions">
                    <button onclick="viewTranscript('${t.filename}')" title="View">👁</button>
                    <button onclick="removeTranscript('${t.filename}')" title="Delete">🗑</button>
                </div>
            `;
            DOM.transcriptsList.appendChild(div);
        });
        
    } catch (error) {
        console.error('Failed to load transcripts:', error);
    }
}

async function viewTranscript(filename) {
    try {
        const data = await SpeecheeAPI.getTranscriptContent(filename);
        displayResult({ success: true, text: data.content, model: 'loaded' });
        showToast('Transcript loaded');
    } catch (error) {
        showToast('Failed to load transcript', 'error');
    }
}

async function removeTranscript(filename) {
    if (!confirm(`Delete ${filename}?`)) return;
    try {
        await SpeecheeAPI.deleteTranscript(filename);
        showToast('Transcript deleted');
        loadTranscripts();
    } catch (error) {
        showToast('Failed to delete', 'error');
    }
}

// ========================================
// LANGUAGE DETECTION
// ========================================
async function detectLanguage() {
    const text = DOM.langInput.value.trim();
    if (!text) {
        showToast('Enter text to detect', 'warning');
        return;
    }
    
    try {
        const data = await SpeecheeAPI.detectLanguage(text);
        
        DOM.langResult.classList.remove('hidden');
        DOM.langResult.innerHTML = `
            <div class="lang-detected">
                <span class="lang-flag">${getLangFlag(data.detected.code)}</span>
                <div>
                    <strong>${data.detected.name}</strong>
                    <span class="lang-code">(${data.detected.code})</span>
                </div>
            </div>
            <div class="lang-confidence">
                <span>Confidence: ${Math.round(data.detected.confidence * 100)}%</span>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${data.detected.confidence * 100}%"></div>
                </div>
            </div>
            <div class="lang-recommend">
                Recommended Model: <code>${data.recommended_model}</code>
            </div>
            ${data.hinglish?.is_hinglish ? '<div class="hinglish-warning">⚠️ Hinglish detected - Use multilingual model</div>' : ''}
        `;
        
    } catch (error) {
        showToast('Detection failed', 'error');
    }
}

function getLangFlag(code) {
    const flags = { en: '🇺🇸', hi: '🇮🇳', es: '🇪🇸', fr: '🇫🇷', de: '🇩🇪', ja: '🇯🇵', ko: '🇰🇷', zh: '🇨🇳' };
    return flags[code] || '🌐';
}

// ========================================
// FILE UPLOAD
// ========================================
function handleFileDrop(e) {
    e.preventDefault();
    DOM.dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
}

function handleFileSelect(file) {
    if (!file) return;
    
    State.currentFile = file;
    DOM.dropZone.classList.add('has-file');
    DOM.fileInfo.classList.remove('hidden');
    DOM.fileName.textContent = file.name;
    DOM.fileSize.textContent = formatBytes(file.size);
    DOM.transcribeBtn.disabled = false;
}

function removeFile() {
    State.currentFile = null;
    DOM.dropZone.classList.remove('has-file');
    DOM.fileInfo.classList.add('hidden');
    DOM.transcribeBtn.disabled = true;
    DOM.fileInput.value = '';
}

// ========================================
// TRANSCRIPTION
// ========================================
async function transcribeFile() {
    if (!State.currentFile) return;
    
    const model = DOM.modelSelect.value;
    const language = DOM.languageSelect.value;
    
    showLoader('Transcribing audio...');
    
    try {
        const result = await SpeecheeAPI.transcribeFile(State.currentFile, model, language);
        
        if (result.success) {
            displayResult(result);
            showToast('Transcription complete!');
            loadTranscripts();
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
        
    } catch (error) {
        showToast('Transcription failed', 'error');
    } finally {
        hideLoader();
    }
}

function displayResult(result) {
    State.lastResult = result;
    DOM.resultPlaceholder.classList.add('hidden');
    DOM.resultText.classList.remove('hidden');
    DOM.resultText.textContent = result.text;
    DOM.resultMeta.classList.remove('hidden');
    DOM.resultMeta.innerHTML = `
        ${result.model ? `<span class="meta-tag">🧠 ${result.model}</span>` : ''}
        ${result.language ? `<span class="meta-tag">🌐 ${result.language}</span>` : ''}
        ${result.processing_time_sec ? `<span class="meta-tag">⏱️ ${result.processing_time_sec}s</span>` : ''}
    `;
}

function clearResult() {
    State.lastResult = null;
    DOM.resultPlaceholder.classList.remove('hidden');
    DOM.resultText.classList.add('hidden');
    DOM.resultMeta.classList.add('hidden');
}

// ========================================
// RECORDING
// ========================================
async function toggleRecording() {
    if (State.isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        State.mediaRecorder = new MediaRecorder(stream);
        State.audioChunks = [];
        
        State.mediaRecorder.ondataavailable = (e) => State.audioChunks.push(e.data);
        State.mediaRecorder.onstop = processRecording;
        
        State.mediaRecorder.start();
        State.isRecording = true;
        State.recordingSeconds = 0;
        
        DOM.recordBtn.classList.add('recording');
        DOM.recordStatus.textContent = 'Recording... Click to stop';
        
        State.recordingTimer = setInterval(() => {
            State.recordingSeconds++;
            DOM.recordTimer.textContent = formatTime(State.recordingSeconds);
            updateWaveform();
            
            const maxDuration = parseInt(DOM.durationSelect.value);
            if (State.recordingSeconds >= maxDuration) stopRecording();
        }, 1000);
        
        initWaveform();
        
    } catch (error) {
        showToast('Microphone access denied', 'error');
    }
}

function stopRecording() {
    if (State.mediaRecorder && State.isRecording) {
        State.mediaRecorder.stop();
        State.mediaRecorder.stream.getTracks().forEach(t => t.stop());
        State.isRecording = false;
        clearInterval(State.recordingTimer);
        
        DOM.recordBtn.classList.remove('recording');
        DOM.recordStatus.textContent = 'Processing...';
    }
}

async function processRecording() {
    const audioBlob = new Blob(State.audioChunks, { type: 'audio/wav' });
    const model = DOM.modelSelect.value;
    
    showLoader('Transcribing recording...');
    
    try {
        const result = await SpeecheeAPI.transcribeFile(audioBlob, model, 'auto');
        
        if (result.success) {
            displayResult(result);
            showToast('Recording transcribed!');
            loadTranscripts();
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
        
    } catch (error) {
        showToast('Processing failed', 'error');
    } finally {
        hideLoader();
        DOM.recordStatus.textContent = 'Click to record';
        DOM.recordTimer.textContent = '00:00';
    }
}

function initWaveform() {
    DOM.waveform.innerHTML = '';
    for (let i = 0; i < 40; i++) {
        const bar = document.createElement('div');
        bar.className = 'wave-bar';
        DOM.waveform.appendChild(bar);
    }
}

function updateWaveform() {
    document.querySelectorAll('.wave-bar').forEach(bar => {
        bar.style.height = (Math.random() * 40 + 5) + 'px';
    });
}

// ========================================
// RESULT ACTIONS
// ========================================
function copyResult() {
    if (!State.lastResult) return;
    navigator.clipboard.writeText(State.lastResult.text);
    showToast('Copied to clipboard');
}

function downloadTxt() {
    if (!State.lastResult) return;
    const blob = new Blob([State.lastResult.text], { type: 'text/plain' });
    downloadBlob(blob, `transcript_${Date.now()}.txt`);
}

function downloadJson() {
    if (!State.lastResult) return;
    const blob = new Blob([JSON.stringify(State.lastResult, null, 2)], { type: 'application/json' });
    downloadBlob(blob, `transcript_${Date.now()}.json`);
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// ========================================
// INITIALIZATION
// ========================================
function initApp() {
    // Load all data
    loadSystemStatus();
    loadModels();
    loadDevices();
    loadConfig();
    loadTranscripts();
    initWaveform();
    
    // Event Listeners
    DOM.dropZone.onclick = () => DOM.fileInput.click();
    DOM.dropZone.ondragover = (e) => { e.preventDefault(); DOM.dropZone.classList.add('dragover'); };
    DOM.dropZone.ondragleave = () => DOM.dropZone.classList.remove('dragover');
    DOM.dropZone.ondrop = handleFileDrop;
    DOM.fileInput.onchange = (e) => handleFileSelect(e.target.files[0]);
    
    DOM.transcribeBtn.onclick = transcribeFile;
    DOM.recordBtn.onclick = toggleRecording;
    DOM.langDetectBtn.onclick = detectLanguage;
    DOM.langInput.onkeypress = (e) => { if (e.key === 'Enter') detectLanguage(); };
    
    document.getElementById('copy-btn').onclick = copyResult;
    document.getElementById('download-txt-btn').onclick = downloadTxt;
    document.getElementById('download-json-btn').onclick = downloadJson;
    document.getElementById('clear-btn').onclick = clearResult;
    document.getElementById('remove-file-btn').onclick = removeFile;
    document.getElementById('refresh-btn').onclick = () => {
        loadSystemStatus();
        loadModels();
        loadDevices();
        showToast('Refreshed');
    };
}

// Start app when DOM ready
document.addEventListener('DOMContentLoaded', initApp);