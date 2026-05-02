/**
 * FlowGuard AI - Production-Grade JavaScript
 * Handles live updates, notifications, and interactive features
 */

// ============================================
// Live Clock Update
// ============================================

function updateClock() {
    const clockElement = document.getElementById('live-clock');
    if (!clockElement) return;
    
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    clockElement.textContent = `${hours}:${minutes}:${seconds}`;
}

// Update clock immediately and then every second
updateClock();
setInterval(updateClock, 1000);

// ============================================
// Toast Notification System
// ============================================

class ToastManager {
    constructor() {
        this.container = document.getElementById('toast-container');
        this.toasts = [];
    }
    
    show(message, type = 'info', duration = 5000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        this.toasts.push(toast);
        
        // Trigger animation
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toast);
            }, duration);
        }
        
        return toast;
    }
    
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease-out';
        
        const icon = this.getIcon(type);
        const color = this.getColor(type);
        
        toast.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <svg class="w-5 h-5" style="color: ${color}" fill="currentColor" viewBox="0 0 20 20">
                        ${icon}
                    </svg>
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-white">${message}</p>
                </div>
                <button onclick="toastManager.remove(this.closest('.toast'))" class="flex-shrink-0 text-gray-400 hover:text-white transition-colors">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        `;
        
        return toast;
    }
    
    getIcon(type) {
        const icons = {
            success: '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>',
            error: '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>',
            warning: '<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>',
            info: '<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>'
        };
        return icons[type] || icons.info;
    }
    
    getColor(type) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        return colors[type] || colors.info;
    }
    
    remove(toast) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            const index = this.toasts.indexOf(toast);
            if (index > -1) {
                this.toasts.splice(index, 1);
            }
        }, 300);
    }
    
    clear() {
        this.toasts.forEach(toast => this.remove(toast));
    }
}

// Initialize toast manager
const toastManager = new ToastManager();

// ============================================
// Autonomous Mode Toggle
// ============================================

function initAutonomousToggle() {
    const toggleButton = document.getElementById('autonomous-toggle');
    if (!toggleButton) return;
    
    let isAutonomous = true;
    
    toggleButton.addEventListener('click', () => {
        isAutonomous = !isAutonomous;
        
        const statusDot = toggleButton.querySelector('.w-2');
        const statusText = toggleButton.querySelector('span');
        
        if (isAutonomous) {
            statusDot.className = 'w-2 h-2 rounded-full bg-accent-green animate-pulse';
            statusText.textContent = 'Autonomous';
            toastManager.show('Autonomous mode enabled', 'success');
        } else {
            statusDot.className = 'w-2 h-2 rounded-full bg-accent-yellow';
            statusText.textContent = 'Manual';
            toastManager.show('Switched to manual mode', 'warning');
        }
        
        // Trigger sound effect for critical state changes
        playNotificationSound();
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initAutonomousToggle);

// ============================================
// Sound Effects (Optional)
// ============================================

function playNotificationSound() {
    // Create a simple beep sound using Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
        // Silently fail if audio context is not supported
        console.log('Audio notification not supported');
    }
}

function playCriticalAlert() {
    // More urgent sound for critical alerts
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 1200;
        oscillator.type = 'square';
        
        gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
    } catch (e) {
        console.log('Audio notification not supported');
    }
}

// ============================================
// HTMX Event Handlers
// ============================================

// Show loading state during HTMX requests
document.body.addEventListener('htmx:beforeRequest', (event) => {
    const target = event.detail.target;
    if (target) {
        target.style.opacity = '0.6';
        target.style.pointerEvents = 'none';
    }
});

document.body.addEventListener('htmx:afterRequest', (event) => {
    const target = event.detail.target;
    if (target) {
        target.style.opacity = '1';
        target.style.pointerEvents = 'auto';
    }
});

// Handle HTMX errors
document.body.addEventListener('htmx:responseError', (event) => {
    toastManager.show('Failed to load data. Please try again.', 'error');
});

// ============================================
// Utility Functions
// ============================================

/**
 * Format timestamp to relative time (e.g., "2 minutes ago")
 */
function formatRelativeTime(timestamp) {
    const now = new Date();
    const past = new Date(timestamp);
    const diffMs = now - past;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
}

/**
 * Format number with commas (e.g., 1000 -> 1,000)
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        toastManager.show('Copied to clipboard', 'success', 2000);
    } catch (err) {
        toastManager.show('Failed to copy', 'error', 2000);
    }
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================
// Auto-refresh for live data
// ============================================

function enableAutoRefresh(selector, interval = 30000) {
    const elements = document.querySelectorAll(selector);
    
    elements.forEach(element => {
        if (element.hasAttribute('hx-get')) {
            setInterval(() => {
                htmx.trigger(element, 'refresh');
            }, interval);
        }
    });
}

// Enable auto-refresh for elements with data-auto-refresh attribute
document.addEventListener('DOMContentLoaded', () => {
    enableAutoRefresh('[data-auto-refresh]');
});

// ============================================
// Export functions for global use
// ============================================

window.FlowGuardAI = {
    toast: toastManager,
    formatRelativeTime,
    formatNumber,
    formatBytes,
    copyToClipboard,
    debounce,
    playNotificationSound,
    playCriticalAlert
};

console.log('🛡️ FlowGuard AI initialized');

// Made with Bob
