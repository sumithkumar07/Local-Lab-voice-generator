/**
 * Voice Generator - Frontend JavaScript
 * Handles TTS generation, audio playback, voice preview, and UI interactions
 * Version 2.0.0
 */

// ============================================
// State Management
// ============================================

const state = {
    selectedVoice: 'am_michael',
    speed: 1.0,
    isGenerating: false,
    currentAudioUrl: null,
    currentAudioUrlMp3: null,
    voices: {},
    previewAudio: null,
    previewTimeout: null,
    currentModel: 'kokoro', // 'kokoro' or 'pro'
    hardware: null
};

// ============================================
// DOM Elements
// ============================================

const elements = {
    textInput: document.getElementById('textInput'),
    charCount: document.getElementById('charCount'),
    voiceGrid: document.getElementById('voiceGrid'),
    speedSlider: document.getElementById('speedSlider'),
    speedValue: document.getElementById('speedValue'),
    generateBtn: document.getElementById('generateBtn'),

    // Audio elements
    audioContainer: document.getElementById('audioContainer'),
    emptyState: document.getElementById('emptyState'),
    audioPlayer: document.getElementById('audioPlayer'),
    audioElement: document.getElementById('audioElement'),
    loadingState: document.getElementById('loadingState'),
    waveform: document.getElementById('waveform'),
    audioDuration: document.getElementById('audioDuration'),
    voiceUsed: document.getElementById('voiceUsed'),
    downloadBtn: document.getElementById('downloadBtn'),
    downloadMp3Btn: document.getElementById('downloadMp3Btn'),
    copyBtn: document.getElementById('copyBtn'),
    modelBadge: document.querySelector('.model-badge'),

    // Toast
    toast: document.getElementById('toast')
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Check Hardware
    checkHardwareStatus();

    // Load voices from API
    await loadVoices();

    // Set up event listeners
    setupEventListeners();

    // Initialize character count
    updateCharCount();

    // Create preview audio element
    state.previewAudio = new Audio();
    state.previewAudio.volume = 0.7;

    console.log('🎙️ Voice Generator v2.0 initialized');
}

// ============================================
// API Functions
// ============================================

async function checkHardwareStatus() {
    try {
        const response = await fetch('/api/system');
        const data = await response.json();

        // Update Badge
        const badge = elements.modelBadge;
        if (badge) {
            state.hardware = data; // Store for later logic

            if (data.platform === 'GPU_READY') {
                badge.innerHTML = `<span class="badge-dot" style="background:#4ade80; box-shadow:0 0 8px #4ade80"></span> GPU Active (Pro)`;
                badge.style.color = '#4ade80';
                badge.style.borderColor = 'rgba(74, 222, 128, 0.3)';
                badge.title = data.message;

                // Enable Pro Toggle
                const proCard = document.getElementById('model-pro');
                if (proCard) {
                    proCard.classList.remove('disabled');
                    document.getElementById('pro-lock').classList.add('hidden');
                }

            } else if (data.platform === 'GPU_DRIVER_MISSING') {
                badge.innerHTML = `<span class="badge-dot" style="background:#f59e0b; box-shadow:0 0 8px #f59e0b"></span> Driver Issue`;
                badge.style.color = '#f59e0b';
                badge.style.borderColor = 'rgba(245, 158, 11, 0.3)';
                badge.title = data.message;

                // Show Driver Alert
                const alert = document.getElementById('driverAlert');
                if (alert) alert.classList.remove('hidden');

                // Disable Pro (or keep valid but warn?) - Let's disable for safety
                // Or maybe allow clicking to see the alert?
                // Decided: Disable visual, but show alert.
                const proCard = document.getElementById('model-pro');
                if (proCard) {
                    proCard.classList.add('disabled');
                    // Update Text to say "Driver Missing"
                    const proTitle = proCard.querySelector('h3');
                    if (proTitle) proTitle.textContent = "🔒 Drivers Missing";
                }

            } else {
                badge.innerHTML = `<span class="badge-dot" style="background:#94a3b8"></span> CPU Mode`;
                badge.style.color = '#94a3b8';
                badge.style.borderColor = 'rgba(148, 163, 184, 0.3)';
                badge.title = data.message;

                // Disable Pro
                const proCard = document.getElementById('model-pro');
                if (proCard) {
                    proCard.classList.add('disabled');
                    document.getElementById('pro-lock').classList.remove('hidden');
                }
            }
        }
    } catch (e) {
        console.error("Failed to check hardware:", e);
    }
}

function selectModel(modelType) {
    if (modelType === state.currentModel) return;

    // Validation
    if (modelType === 'pro') {
        if (!state.hardware || !state.hardware.can_run_pro) {
            if (state.hardware && state.hardware.platform === 'GPU_DRIVER_MISSING') {
                showToast("Please install NVIDIA drivers first", "warning");
                // Ensure alert is visible
                document.getElementById('driverAlert').classList.remove('hidden');
            } else {
                showToast("Pro Mode requires an NVIDIA GPU", "error");
            }
            return;
        }
    }

    // Switch State
    state.currentModel = modelType;

    // Update UI
    document.getElementById('model-kokoro').classList.toggle('active', modelType === 'kokoro');
    document.getElementById('model-pro').classList.toggle('active', modelType === 'pro');

    showToast(`Switched to ${modelType === 'pro' ? 'Pro' : 'Standard'} Engine`, 'success');
}

async function loadVoices() {
    try {
        const response = await fetch('/api/voices');
        const data = await response.json();

        if (data.success) {
            state.voices = data.voices;
            state.selectedVoice = data.default;
            renderVoiceGrid();
        }
    } catch (error) {
        console.error('Failed to load voices:', error);
        showToast('Failed to load voices. Using defaults.', 'error');

        // Use fallback voices
        state.voices = {
            'am_michael': { name: 'Michael', gender: 'Male', accent: 'American', style: 'Narrator' },
            'af_heart': { name: 'Heart', gender: 'Female', accent: 'American', style: 'Warm' }
        };
        renderVoiceGrid();
    }
}

async function generateVoice() {
    const text = elements.textInput.value.trim();

    // Validation
    if (!text) {
        showToast('Please enter some text first', 'error');
        return;
    }

    if (text.length > 10000) {
        showToast('Text is too long (max 10,000 characters)', 'error');
        return;
    }

    // Set loading state
    state.isGenerating = true;
    updateUIState();

    try {
        const response = await fetch('/api/synthesize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                voice: state.selectedVoice,
                speed: state.speed,
                format: 'wav',
                model: state.currentModel
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Generation failed');
        }

        if (data.success) {
            // Store audio URLs
            state.currentAudioUrl = data.audio_url;
            state.currentAudioUrlMp3 = data.audio_url_mp3;

            // Update audio player
            elements.audioElement.src = data.audio_url;
            elements.audioDuration.textContent = `Duration: ${formatDuration(data.duration)}`;
            elements.voiceUsed.textContent = `Voice: ${state.voices[state.selectedVoice]?.name || state.selectedVoice}`;

            // Show/hide MP3 button based on availability
            if (elements.downloadMp3Btn) {
                elements.downloadMp3Btn.style.display = data.audio_url_mp3 ? 'flex' : 'none';
            }

            // Show player
            showAudioPlayer();

            // Auto-play
            elements.audioElement.play();

            showToast(`Generated ${formatDuration(data.duration)} of audio!`, 'success');
        }
    } catch (error) {
        console.error('Generation error:', error);
        showToast(error.message || 'Failed to generate audio', 'error');
        showEmptyState();
    } finally {
        state.isGenerating = false;
        updateUIState();
    }
}

// ============================================
// Voice Preview
// ============================================

function playVoicePreview(voiceId) {
    // Clear any pending preview
    if (state.previewTimeout) {
        clearTimeout(state.previewTimeout);
    }

    // Stop current preview if playing
    if (state.previewAudio) {
        state.previewAudio.pause();
        state.previewAudio.currentTime = 0;
    }

    // Delay before playing to avoid rapid fire on quick mouse movements
    state.previewTimeout = setTimeout(() => {
        state.previewAudio.src = `/api/preview/${voiceId}`;
        state.previewAudio.play().catch(e => {
            // Preview might not be generated yet, that's okay
            console.log('Preview not ready or failed:', e.message);
        });
    }, 300);
}

function stopVoicePreview() {
    // Clear pending preview
    if (state.previewTimeout) {
        clearTimeout(state.previewTimeout);
        state.previewTimeout = null;
    }

    // Stop audio
    if (state.previewAudio) {
        state.previewAudio.pause();
        state.previewAudio.currentTime = 0;
    }
}

// ============================================
// UI Rendering
// ============================================

function renderVoiceGrid() {
    elements.voiceGrid.innerHTML = '';

    // Group voices by accent
    const voiceEntries = Object.entries(state.voices);

    voiceEntries.forEach(([id, voice]) => {
        const card = document.createElement('div');
        card.className = `voice-card ${id === state.selectedVoice ? 'selected' : ''}`;
        card.dataset.voiceId = id;

        const genderIcon = voice.gender === 'Female' ? '👩' : '👨';

        card.innerHTML = `
            <div class="voice-name">${genderIcon} ${voice.name}</div>
            <div class="voice-meta">${voice.accent} • ${voice.style}</div>
            <div class="voice-preview-hint">🔊 Hover to preview</div>
        `;

        // Click to select
        card.addEventListener('click', () => selectVoice(id));

        // Hover for preview
        card.addEventListener('mouseenter', () => playVoicePreview(id));
        card.addEventListener('mouseleave', () => stopVoicePreview());

        elements.voiceGrid.appendChild(card);
    });
}

function selectVoice(voiceId) {
    state.selectedVoice = voiceId;

    // Update UI
    document.querySelectorAll('.voice-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.voiceId === voiceId);
    });
}

function updateCharCount() {
    const count = elements.textInput.value.length;
    const max = 10000;

    elements.charCount.textContent = `${count.toLocaleString()} / ${max.toLocaleString()}`;

    // Change color if near limit
    if (count > max * 0.9) {
        elements.charCount.style.color = 'var(--error)';
    } else if (count > max * 0.7) {
        elements.charCount.style.color = 'var(--warning)';
    } else {
        elements.charCount.style.color = 'var(--text-muted)';
    }
}

function updateUIState() {
    // Update button state
    elements.generateBtn.disabled = state.isGenerating;
    elements.generateBtn.querySelector('.btn-text').textContent =
        state.isGenerating ? 'Generating...' : 'Generate Voice';

    // Show/hide loading state
    if (state.isGenerating) {
        showLoadingState();
    }
}

function showEmptyState() {
    elements.emptyState.classList.remove('hidden');
    elements.audioPlayer.classList.add('hidden');
    elements.loadingState.classList.add('hidden');
}

function showLoadingState() {
    elements.emptyState.classList.add('hidden');
    elements.audioPlayer.classList.add('hidden');
    elements.loadingState.classList.remove('hidden');
}

function showAudioPlayer() {
    elements.emptyState.classList.add('hidden');
    elements.loadingState.classList.add('hidden');
    elements.audioPlayer.classList.remove('hidden');
}

// ============================================
// Event Listeners
// ============================================

function setupEventListeners() {
    // Text input
    elements.textInput.addEventListener('input', updateCharCount);

    // Speed slider
    elements.speedSlider.addEventListener('input', (e) => {
        state.speed = parseFloat(e.target.value);
        elements.speedValue.textContent = `${state.speed.toFixed(1)}x`;
    });

    // Generate button
    elements.generateBtn.addEventListener('click', generateVoice);

    // Keyboard shortcut (Ctrl+Enter to generate)
    elements.textInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            generateVoice();
        }
    });

    // Audio player events
    elements.audioElement.addEventListener('play', () => {
        elements.waveform.classList.remove('paused');
    });

    elements.audioElement.addEventListener('pause', () => {
        elements.waveform.classList.add('paused');
    });

    elements.audioElement.addEventListener('ended', () => {
        elements.waveform.classList.add('paused');
    });

    // Download WAV button
    elements.downloadBtn.addEventListener('click', () => downloadAudio('wav'));

    // Download MP3 button
    if (elements.downloadMp3Btn) {
        elements.downloadMp3Btn.addEventListener('click', () => downloadAudio('mp3'));
    }

    // Copy link button
    elements.copyBtn.addEventListener('click', copyAudioLink);
}

// ============================================
// Audio Actions
// ============================================

function downloadAudio(format = 'wav') {
    const url = format === 'mp3' ? state.currentAudioUrlMp3 : state.currentAudioUrl;

    if (!url) {
        showToast(`No ${format.toUpperCase()} audio to download`, 'error');
        return;
    }

    const link = document.createElement('a');
    link.href = url;
    link.download = `voice_${Date.now()}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast(`${format.toUpperCase()} download started!`, 'success');
}

function copyAudioLink() {
    if (!state.currentAudioUrl) {
        showToast('No audio link to copy', 'error');
        return;
    }

    const fullUrl = window.location.origin + state.currentAudioUrl;

    navigator.clipboard.writeText(fullUrl)
        .then(() => showToast('Link copied to clipboard!', 'success'))
        .catch(() => showToast('Failed to copy link', 'error'));
}

// ============================================
// Utility Functions
// ============================================

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);

    if (mins > 0) {
        return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
}

function showToast(message, type = 'info') {
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️'
    };

    elements.toast.querySelector('.toast-icon').textContent = icons[type] || icons.info;
    elements.toast.querySelector('.toast-message').textContent = message;
    elements.toast.className = `toast ${type}`;

    // Show toast
    elements.toast.classList.remove('hidden');
    requestAnimationFrame(() => {
        elements.toast.classList.add('show');
    });

    // Hide after 4 seconds
    setTimeout(() => {
        elements.toast.classList.remove('show');
        setTimeout(() => {
            elements.toast.classList.add('hidden');
        }, 300);
    }, 4000);
}

// ============================================
// Debug Helper
// ============================================

window.voiceApp = {
    state,
    generateVoice,
    loadVoices,
    playVoicePreview,
    stopVoicePreview
};
