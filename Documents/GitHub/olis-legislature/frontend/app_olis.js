/**
 * OLIS Application JavaScript
 * Handles Oregon Legislative Information System interactions
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// State
let sessions = [];
let currentSession = null;
let currentStats = null;

// Enhanced Error Handling Functions
class ApiError extends Error {
    constructor(message, code, status, details) {
        super(message);
        this.name = 'ApiError';
        this.code = code;
        this.status = status;
        this.details = details;
    }
}

async function makeApiRequest(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout for OLIS
    
    const requestOptions = {
        signal: controller.signal,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };
    
    try {
        const response = await fetch(url, requestOptions);
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                throw new ApiError(
                    `HTTP ${response.status}`, 
                    'HTTP_ERROR', 
                    response.status,
                    response.statusText
                );
            }
            
            throw new ApiError(
                errorData.error?.message || `HTTP ${response.status}`,
                errorData.error?.code || 'HTTP_ERROR',
                response.status,
                errorData.error?.details || response.statusText
            );
        }
        
        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new ApiError('Request timed out', 'TIMEOUT', 408, 'The request took too long to complete');
        }
        if (error instanceof ApiError) {
            throw error;
        }
        throw new ApiError('Network error', 'NETWORK_ERROR', 0, error.message);
    }
}

// UI Helper Functions
function updateConnectionStatus(status, message = null) {
    const statusElement = document.getElementById('connection-status');
    const textElement = document.getElementById('connection-text');
    
    if (statusElement && textElement) {
        statusElement.className = `status-dot ${status}`;
        
        switch (status) {
            case 'running':
                textElement.textContent = message || 'Connected to OLIS';
                break;
            case 'pending':
                textElement.textContent = message || 'Connecting to OLIS...';
                break;
            case 'error':
                textElement.textContent = message || 'Connection failed';
                break;
            default:
                textElement.textContent = message || 'Unknown status';
        }
    }
}

function showAlert(type, title, message) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    
    alertContainer.className = 'alert-container';
    alertContainer.innerHTML = `
        <div class="alert alert-${type}">
            <div class="alert-content">
                <div class="alert-title">${title}</div>
                <div>${message}</div>
            </div>
        </div>
    `;
    
    // Auto-hide after 5 seconds for non-error alerts
    if (type !== 'error') {
        setTimeout(() => {
            if (alertContainer) {
                alertContainer.className = 'alert-container-hidden';
            }
        }, 5000);
    }
}

function hideAlert() {
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        alertContainer.className = 'alert-container-hidden';
    }
}

// OLIS API Functions
async function loadSessions() {
    try {
        updateConnectionStatus('pending', 'Loading sessions...');
        const response = await makeApiRequest(`${API_BASE_URL}/sessions`);
        
        if (response.success && response.data?.sessions) {
            sessions = response.data.sessions;
            populateSessionSelector();
            updateConnectionStatus('running');
            
            // Auto-select the most recent session
            if (sessions.length > 0) {
                const mostRecent = sessions.reduce((latest, session) => {
                    return new Date(session.BeginDate) > new Date(latest.BeginDate) ? session : latest;
                });
                selectSession(mostRecent.SessionKey);
            }
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
        updateConnectionStatus('error', `Failed to load sessions: ${error.message}`);
        showAlert('error', 'Connection Error', 'Could not load legislative sessions. Please check your connection and try again.');
    }
}

function populateSessionSelector() {
    const selector = document.getElementById('session-selector');
    if (!selector) return;
    
    selector.innerHTML = '<option value="">Select a session...</option>';
    
    // Sort sessions by begin date (most recent first)
    const sortedSessions = [...sessions].sort((a, b) => 
        new Date(b.BeginDate) - new Date(a.BeginDate)
    );
    
    sortedSessions.forEach(session => {
        const option = document.createElement('option');
        option.value = session.SessionKey;
        option.textContent = `${session.SessionName} (${new Date(session.BeginDate).getFullYear()})`;
        selector.appendChild(option);
    });
}

async function loadSessionStats(sessionKey) {
    if (!sessionKey) return;
    
    try {
        hideAlert();
        updateSessionDisplay(sessionKey, 'Loading statistics...');
        showLoadingStats();
        
        const response = await makeApiRequest(`${API_BASE_URL}/sessions/${encodeURIComponent(sessionKey)}/stats`);
        
        if (response.success && response.data) {
            currentStats = response.data;
            displayStats(response.data);
            
            // Load hot bills after stats are loaded
            loadHotBills(sessionKey);
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Failed to load session stats:', error);
        showAlert('error', 'Data Error', `Could not load statistics for this session: ${error.message}`);
        hideStats();
    }
}

async function loadHotBills(sessionKey, limit = 6) {
    if (!sessionKey) return;
    
    try {
        const response = await makeApiRequest(`${API_BASE_URL}/sessions/${encodeURIComponent(sessionKey)}/hot-bills?limit=${limit}`);
        
        if (response.success && response.data) {
            displayHotBills(response.data);
        } else {
            throw new Error('Invalid hot bills response format');
        }
    } catch (error) {
        console.error('Failed to load hot bills:', error);
        hideHotBills();
    }
}

function updateSessionDisplay(sessionKey, status = null) {
    const session = sessions.find(s => s.SessionKey === sessionKey);
    const sessionNameElement = document.getElementById('session-name');
    
    if (sessionNameElement && session) {
        if (status) {
            sessionNameElement.textContent = status;
        } else {
            sessionNameElement.textContent = `${session.SessionName} (${new Date(session.BeginDate).getFullYear()})`;
        }
    }
}

function showLoadingStats() {
    const statsContent = document.getElementById('stats-content');
    const billBreakdown = document.getElementById('bill-breakdown');
    
    if (statsContent) {
        statsContent.innerHTML = `
            <div class="flex justify-center items-center py-16">
                <div class="text-center">
                    <div class="spinner"></div>
                    <p class="text-secondary mt-4">Loading session statistics...</p>
                </div>
            </div>
        `;
    }
    
    if (billBreakdown) {
        billBreakdown.style.display = 'none';
    }
}

function displayStats(stats) {
    const statsContent = document.getElementById('stats-content');
    const billBreakdown = document.getElementById('bill-breakdown');
    
    if (statsContent) {
        statsContent.innerHTML = `
            <div class="grid-3">
                <div class="stat-item">
                    <div class="stat-number">${stats.total_bills || 0}</div>
                    <div class="stat-label">Total Bills</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${stats.status_counts?.active || 0}</div>
                    <div class="stat-label">Active</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${stats.status_counts?.passed || 0}</div>
                    <div class="stat-label">Passed</div>
                </div>
            </div>
        `;
    }
    
    // Update detailed breakdown
    if (billBreakdown && stats.status_counts) {
        document.getElementById('total-bills').textContent = stats.total_bills || 0;
        document.getElementById('active-bills').textContent = stats.status_counts.active || 0;
        document.getElementById('passed-bills').textContent = stats.status_counts.passed || 0;
        document.getElementById('failed-bills').textContent = stats.status_counts.failed || 0;
        document.getElementById('pending-bills').textContent = stats.status_counts.pending || 0;
        document.getElementById('other-bills').textContent = stats.status_counts.other || 0;
        
        billBreakdown.style.display = 'block';
    }
}

function hideStats() {
    const statsContent = document.getElementById('stats-content');
    const billBreakdown = document.getElementById('bill-breakdown');
    
    if (statsContent) {
        statsContent.innerHTML = `
            <div class="flex justify-center items-center py-16">
                <div class="text-center">
                    <div class="text-tertiary">❌</div>
                    <p class="text-secondary">Unable to load session statistics</p>
                </div>
            </div>
        `;
    }
    
    if (billBreakdown) {
        billBreakdown.style.display = 'none';
    }
}

function displayHotBills(hotBillsData) {
    const hotBillsSection = document.getElementById('hot-bills-section');
    const hotBillsGrid = document.getElementById('hot-bills-grid');
    
    if (!hotBillsGrid) return;
    
    if (!hotBillsData.hot_bills || hotBillsData.hot_bills.length === 0) {
        hideHotBills();
        return;
    }
    
    // Clear existing content
    hotBillsGrid.innerHTML = '';
    
    // Create hot bill buttons with status badges
    hotBillsData.hot_bills.forEach(bill => {
        const billContainer = document.createElement('div');
        billContainer.className = 'hot-bill-container';
        
        // Get status display information
        const statusDisplay = bill.status_display || { display_name: 'Unknown', color: 'secondary' };
        const statusClass = `status-${statusDisplay.color || 'secondary'}`;
        
        billContainer.innerHTML = `
            <button class="olis-button bill-button" data-bill-id="${bill.bill_id}">
                <div class="bill-header">
                    <div class="bill-id-with-status">
                        <span class="bill-id">${bill.bill_id}</span>
                        <span class="bill-status-badge ${statusClass}">${statusDisplay.display_name}</span>
                    </div>
                    <div class="heat-indicator">
                        <span class="heat-emoji">${bill.heat_emoji}</span>
                        <span class="heat-level">${bill.heat_level}</span>
                    </div>
                </div>
                <div class="bill-title">${bill.title}</div>
                <div class="bill-stats">
                    <div class="stat-item">
                        <span class="stat-number">${bill.testimony_count}</span>
                        <span class="stat-label">testimonies</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${bill.total_unique_submitters}</span>
                        <span class="stat-label">submitters</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${Math.round(bill.hotness_score)}</span>
                        <span class="stat-label">hotness</span>
                    </div>
                </div>
                <div class="details-toggle" style="display: none;">
                    <span class="toggle-text">Details</span>
                    <span class="toggle-arrow">▼</span>
                </div>
            </button>
            <div class="bill-details" style="display: none;">
                <!-- Detailed bill information will be populated here when expanded -->
                <div class="details-loading">Loading details...</div>
            </div>
        `;
        
        hotBillsGrid.appendChild(billContainer);
    });
    
    // Show the hot bills section
    if (hotBillsSection) {
        hotBillsSection.style.display = 'block';
    }
}

function hideHotBills() {
    const hotBillsSection = document.getElementById('hot-bills-section');
    const hotBillsGrid = document.getElementById('hot-bills-grid');
    
    if (hotBillsGrid) {
        hotBillsGrid.innerHTML = `
            <div class="flex justify-center items-center py-8">
                <div class="text-center">
                    <div class="text-tertiary">📊</div>
                    <p class="text-secondary">No hot bills data available</p>
                </div>
            </div>
        `;
    }
    
    if (hotBillsSection) {
        hotBillsSection.style.display = 'none';
    }
}

function selectSession(sessionKey) {
    if (!sessionKey) {
        hideStats();
        return;
    }
    
    currentSession = sessionKey;
    
    // Update selector if not already selected
    const selector = document.getElementById('session-selector');
    if (selector && selector.value !== sessionKey) {
        selector.value = sessionKey;
    }
    
    updateSessionDisplay(sessionKey);
    loadSessionStats(sessionKey);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Session selector change handler
    const sessionSelector = document.getElementById('session-selector');
    if (sessionSelector) {
        sessionSelector.addEventListener('change', function(e) {
            selectSession(e.target.value);
        });
    }
    
    // Load initial data
    loadSessions();
});

// Export functions for potential external use
window.OLIS = {
    loadSessions,
    loadSessionStats,
    loadHotBills,
    selectSession,
    updateConnectionStatus,
    showAlert,
    hideAlert
};