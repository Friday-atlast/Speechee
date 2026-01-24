/**
 * Speechee API Client
 * Each endpoint has its own dedicated method
 * Provided by Friday
 */

const API = {
    BASE_URL: window.location.origin,

    // ========================================
    // SYSTEM ENDPOINTS
    // ========================================

    /**
     * Get API root information
     */
    async getInfo() {
        const response = await fetch(`${this.BASE_URL}/`);
        return await response.json();
    },

    /**
     * Check system health status
     */
    async getHealth() {
        const response = await fetch(`${this.BASE_URL}/health`);
        return await response.json();
    },

    // ========================================
    // TRANSCRIPTION ENDPOINTS
    // ========================================

    /**
     * Transcribe audio file
     * @param {File} file - Audio file
     * @param {string} model - Model name
     * @param {string} language - Language code
     */
    async transcribeFile(file, model = 'tiny.en', language = 'auto') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('model', model);
        formData.append('language', language);

        const response = await fetch(`${this.BASE_URL}/stt`, {
            method: 'POST',
            body: formData
        });
        return await response.json();
    },

    /**
     * Record from microphone and transcribe
     * @param {number} duration - Recording duration in seconds
     * @param {string} model - Model name
     */
    async recordAndTranscribe(duration = 5, model = 'tiny.en') {
        const response = await fetch(`${this.BASE_URL}/listen`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration, model, language: 'auto' })
        });
        return await response.json();
    },

    // ========================================
    // MODEL ENDPOINTS
    // ========================================

    /**
     * Get all available models
     */
    async getModels() {
        const response = await fetch(`${this.BASE_URL}/models`);
        return await response.json();
    },

    /**
     * Download a specific model
     * @param {string} modelName - Model to download
     */
    async downloadModel(modelName) {
        const response = await fetch(`${this.BASE_URL}/models/${modelName}/download`, {
            method: 'POST'
        });
        return await response.json();
    },

    // ========================================
    // CONFIG ENDPOINTS
    // ========================================

    /**
     * Get full configuration
     */
    async getConfig() {
        const response = await fetch(`${this.BASE_URL}/config`);
        return await response.json();
    },

    /**
     * Get specific config value
     * @param {string} key - Config key (dot notation)
     */
    async getConfigValue(key) {
        const response = await fetch(`${this.BASE_URL}/config/${key}`);
        return await response.json();
    },

    /**
     * Update config value
     * @param {string} key - Config key
     * @param {any} value - New value
     */
    async updateConfig(key, value) {
        const response = await fetch(`${this.BASE_URL}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, value })
        });
        return await response.json();
    },

    // ========================================
    // DEVICE ENDPOINTS
    // ========================================

    /**
     * Get all audio input devices
     */
    async getDevices() {
        const response = await fetch(`${this.BASE_URL}/devices`);
        return await response.json();
    },

    // ========================================
    // TRANSCRIPT ENDPOINTS
    // ========================================

    /**
     * Get saved transcripts list
     * @param {number} limit - Max results
     */
    async getTranscripts(limit = 20) {
        const response = await fetch(`${this.BASE_URL}/transcripts?limit=${limit}`);
        return await response.json();
    },

    /**
     * Get specific transcript content
     * @param {string} filename - Transcript filename
     */
    async getTranscriptContent(filename) {
        const response = await fetch(`${this.BASE_URL}/transcripts/${filename}`);
        return await response.json();
    },

    /**
     * Delete a transcript
     * @param {string} filename - Transcript to delete
     */
    async deleteTranscript(filename) {
        const response = await fetch(`${this.BASE_URL}/transcripts/${filename}`, {
            method: 'DELETE'
        });
        return await response.json();
    },

    // ========================================
    // LANGUAGE ENDPOINTS
    // ========================================

    /**
     * Detect language of text
     * @param {string} text - Text to analyze
     */
    async detectLanguage(text) {
        const response = await fetch(`${this.BASE_URL}/language/detect?text=${encodeURIComponent(text)}`);
        return await response.json();
    },

    /**
     * Get all supported languages
     */
    async getSupportedLanguages() {
        const response = await fetch(`${this.BASE_URL}/language/list`);
        return await response.json();
    },

    /**
     * Get recommended model for language
     * @param {string} langCode - Language code
     * @param {string} quality - fast/balanced/accurate
     */
    async getRecommendedModel(langCode, quality = 'balanced') {
        const response = await fetch(`${this.BASE_URL}/language/model/${langCode}?quality=${quality}`);
        return await response.json();
    }
};

// Export for use
window.SpeecheeAPI = API;