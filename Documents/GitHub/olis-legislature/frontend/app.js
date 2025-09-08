/**
 * OLIS Application JavaScript
 * Handles Oregon Legislative Information System interactions
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8001/api';

// State
let sessions = [];
let currentSession = null;
let currentStats = null;
let currentHotBills = null;

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
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Failed to load session stats:', error);
        showAlert('error', 'Data Error', `Could not load statistics for this session: ${error.message}`);
        hideStats();
    }
}

async function loadHotBills(sessionKey) {
    if (!sessionKey) return;
    
    try {
        console.log('Loading hot bills for session:', sessionKey);
        
        const response = await makeApiRequest(`${API_BASE_URL}/sessions/${encodeURIComponent(sessionKey)}/hot-bills`);
        
        if (response.success && response.data) {
            currentHotBills = response.data;
            displayHotBills(response.data);
        } else {
            throw new Error('Invalid hot bills response format');
        }
    } catch (error) {
        console.error('Failed to load hot bills:', error);
        // Don't show error alert for hot bills - it's a secondary feature
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

function groupBillTypes(billTypeCounts, totalBills) {
    // Group related bill types for a cleaner UI
    const groups = [];
    
    // House Bills
    if (billTypeCounts.HB) {
        groups.push({
            name: 'House Bills',
            count: billTypeCounts.HB,
            percentage: ((billTypeCounts.HB / totalBills) * 100).toFixed(1),
            types: ['HB'],
            description: 'Legislation originating in the House'
        });
    }
    
    // Senate Bills
    if (billTypeCounts.SB) {
        groups.push({
            name: 'Senate Bills', 
            count: billTypeCounts.SB,
            percentage: ((billTypeCounts.SB / totalBills) * 100).toFixed(1),
            types: ['SB'],
            description: 'Legislation originating in the Senate'
        });
    }
    
    // Resolutions (combine concurrent resolutions)
    const resolutionTypes = ['HCR', 'SCR', 'HR', 'SR'];
    const resolutionCount = resolutionTypes.reduce((sum, type) => sum + (billTypeCounts[type] || 0), 0);
    if (resolutionCount > 0) {
        groups.push({
            name: 'Resolutions',
            count: resolutionCount,
            percentage: ((resolutionCount / totalBills) * 100).toFixed(1),
            types: resolutionTypes.filter(type => billTypeCounts[type]),
            description: 'House and Senate resolutions'
        });
    }
    
    // Joint Resolutions (constitutional amendments)
    const jointResTypes = ['HJR', 'SJR'];
    const jointResCount = jointResTypes.reduce((sum, type) => sum + (billTypeCounts[type] || 0), 0);
    if (jointResCount > 0) {
        groups.push({
            name: 'Joint Resolutions',
            count: jointResCount,
            percentage: ((jointResCount / totalBills) * 100).toFixed(1),
            types: jointResTypes.filter(type => billTypeCounts[type]),
            description: 'Constitutional amendments'
        });
    }
    
    // Memorials
    const memorialTypes = ['HJM', 'SJM'];
    const memorialCount = memorialTypes.reduce((sum, type) => sum + (billTypeCounts[type] || 0), 0);
    if (memorialCount > 0) {
        groups.push({
            name: 'Memorials',
            count: memorialCount,
            percentage: ((memorialCount / totalBills) * 100).toFixed(1),
            types: memorialTypes.filter(type => billTypeCounts[type]),
            description: 'Memorials to federal government'
        });
    }
    
    return groups.sort((a, b) => b.count - a.count);
}

function displayStats(stats) {
    // Update total bills count
    const totalCount = document.getElementById('total-bills-count');
    if (totalCount) {
        totalCount.textContent = stats.total_bills || 0;
    }
    
    // Hide loading and show button grids
    const dashboardLoading = document.getElementById('dashboard-loading');
    const statusButtons = document.getElementById('status-buttons');
    const typeButtons = document.getElementById('type-buttons');
    const houseCommitteeButtons = document.getElementById('house-committee-buttons');
    const senateCommitteeButtons = document.getElementById('senate-committee-buttons');
    const jointCommitteeButtons = document.getElementById('joint-committee-buttons');
    const hotBillsSection = document.getElementById('hot-bills-section');
    
    if (dashboardLoading) dashboardLoading.style.display = 'none';
    if (statusButtons) statusButtons.style.display = 'block';
    if (typeButtons) typeButtons.style.display = 'block';
    if (houseCommitteeButtons) houseCommitteeButtons.style.display = 'block';
    if (senateCommitteeButtons) senateCommitteeButtons.style.display = 'block';
    if (jointCommitteeButtons) jointCommitteeButtons.style.display = 'block';
    if (hotBillsSection) hotBillsSection.style.display = 'block';
    
    // Create status buttons (limit to top 8 statuses to keep compact)
    if (stats.status_display) {
        const statusGrid = document.getElementById('status-grid');
        if (statusGrid) {
            const sortedStatuses = Object.entries(stats.status_display)
                .sort((a, b) => b[1].count - a[1].count)
                .slice(0, 8); // Limit to 8 for 2 rows of 4
            
            const statusButtons = sortedStatuses.map(([status, info]) => `
                <button class="bill-button" 
                        data-filter-type="status" 
                        data-filter-value="${status}"
                        title="${info.description}">
                    <span class="bill-count">${info.count}</span>
                    <span class="bill-label">${info.display_name}</span>
                    <span class="bill-percentage">${info.percentage}%</span>
                </button>
            `).join('');
            
            statusGrid.innerHTML = statusButtons;
        }
    }
    
    // Create bill type buttons (group similar types for compactness)
    if (stats.bill_type_counts) {
        const typeGrid = document.getElementById('type-grid');
        if (typeGrid) {
            // Group bill types for better UX
            const groupedTypes = groupBillTypes(stats.bill_type_counts, stats.total_bills);
            
            const typeButtonsHtml = groupedTypes.map(group => `
                <button class="bill-button" 
                        data-filter-type="bill_type" 
                        data-filter-value="${group.types.join(',')}"
                        title="${group.description}">
                    <span class="bill-count">${group.count}</span>
                    <span class="bill-label">${group.name}</span>
                    <span class="bill-percentage">${group.percentage}%</span>
                </button>
            `).join('');
            
            typeGrid.innerHTML = typeButtonsHtml;
        }
    }
    
    // Create specific committee buttons for each chamber
    if (stats.specific_committees) {
        
        // House Committee Buttons
        if (stats.specific_committees.house_committees && stats.specific_committees.house_committees.committees) {
            const houseCommitteeGrid = document.getElementById('house-committee-grid');
            if (houseCommitteeGrid) {
                const houseCommittees = Object.entries(stats.specific_committees.house_committees.committees);
                
                const houseButtonsHtml = houseCommittees.map(([committee_code, info]) => `
                    <button class="bill-button" 
                            data-filter-type="committee" 
                            data-filter-value="${committee_code}"
                            title="${info.description}">
                        <span class="bill-count">${info.count}</span>
                        <span class="bill-label">${info.display_name}</span>
                        <span class="bill-percentage">${info.percentage}% of committee bills</span>
                    </button>
                `).join('');
                
                houseCommitteeGrid.innerHTML = houseButtonsHtml;
            }
        }
        
        // Senate Committee Buttons  
        if (stats.specific_committees.senate_committees && stats.specific_committees.senate_committees.committees) {
            const senateCommitteeGrid = document.getElementById('senate-committee-grid');
            if (senateCommitteeGrid) {
                const senateCommittees = Object.entries(stats.specific_committees.senate_committees.committees);
                
                const senateButtonsHtml = senateCommittees.map(([committee_code, info]) => `
                    <button class="bill-button" 
                            data-filter-type="committee" 
                            data-filter-value="${committee_code}"
                            title="${info.description}">
                        <span class="bill-count">${info.count}</span>
                        <span class="bill-label">${info.display_name}</span>
                        <span class="bill-percentage">${info.percentage}% of committee bills</span>
                    </button>
                `).join('');
                
                senateCommitteeGrid.innerHTML = senateButtonsHtml;
            }
        }
        
        // Joint Committee Buttons
        if (stats.specific_committees.joint_committees && stats.specific_committees.joint_committees.committees) {
            const jointCommitteeGrid = document.getElementById('joint-committee-grid');
            if (jointCommitteeGrid) {
                const jointCommittees = Object.entries(stats.specific_committees.joint_committees.committees);
                
                const jointButtonsHtml = jointCommittees.map(([committee_code, info]) => `
                    <button class="bill-button" 
                            data-filter-type="committee" 
                            data-filter-value="${committee_code}"
                            title="${info.description}">
                        <span class="bill-count">${info.count}</span>
                        <span class="bill-label">${info.display_name}</span>
                        <span class="bill-percentage">${info.percentage}% of committee bills</span>
                    </button>
                `).join('');
                
                jointCommitteeGrid.innerHTML = jointButtonsHtml;
            }
        }
    }
    
}

function displayHotBills(hotBillsData) {
    const hotBillsSection = document.getElementById('hot-bills-section');
    const hotBillsGrid = document.getElementById('hot-bills-grid');
    const hotBillsActions = document.querySelector('.hot-bills-actions');
    
    if (!hotBillsData || !hotBillsData.hot_bills || hotBillsData.hot_bills.length === 0) {
        if (hotBillsSection) hotBillsSection.style.display = 'none';
        return;
    }
    
    // Show the hot bills section
    if (hotBillsSection) hotBillsSection.style.display = 'block';
    
    // Generate hot bill buttons
    if (hotBillsGrid) {
        const hotBillButtons = hotBillsData.hot_bills.map(bill => {
            const heatClass = `heat-${bill.heat_level}`;
            const testimonyText = bill.testimony_count === 1 ? 'testimony' : 'testimonies';
            
            return `
                <button class="bill-button hot-bill-button ${heatClass}" 
                        data-filter-type="hot-bill" 
                        data-filter-value="${bill.bill_id}"
                        title="${bill.title}">
                    <div class="hot-bill-header">
                        <span class="heat-indicator">${bill.heat_emoji}</span>
                        <span class="bill-count">${bill.testimony_count}</span>
                    </div>
                    <span class="bill-label">${bill.bill_id}</span>
                    <span class="bill-percentage">${bill.testimony_count} ${testimonyText}</span>
                    <div class="hotness-score" title="Hotness Score: ${bill.hotness_score}">
                        Score: ${bill.hotness_score}
                    </div>
                </button>
            `;
        }).join('');
        
        hotBillsGrid.innerHTML = hotBillButtons;
    }
    
    // Show "View All" button if there are hot bills
    if (hotBillsActions && hotBillsData.hot_bills.length > 0) {
        hotBillsActions.style.display = 'block';
    }
}

function hideHotBills() {
    const hotBillsSection = document.getElementById('hot-bills-section');
    if (hotBillsSection) {
        hotBillsSection.style.display = 'none';
    }
}

function hideStats() {
    // Reset total bills count
    const totalCount = document.getElementById('total-bills-count');
    if (totalCount) {
        totalCount.textContent = '-';
    }
    
    // Show loading and hide button grids
    const dashboardLoading = document.getElementById('dashboard-loading');
    const statusButtons = document.getElementById('status-buttons');
    const typeButtons = document.getElementById('type-buttons');
    const houseCommitteeButtons = document.getElementById('house-committee-buttons');
    const senateCommitteeButtons = document.getElementById('senate-committee-buttons');
    const jointCommitteeButtons = document.getElementById('joint-committee-buttons');
    const hotBillsSection = document.getElementById('hot-bills-section');
    
    if (dashboardLoading) {
        dashboardLoading.style.display = 'block';
        dashboardLoading.innerHTML = `
            <div class="text-center">
                <div class="text-tertiary">❌</div>
                <p class="text-secondary">Unable to load session statistics</p>
            </div>
        `;
    }
    
    if (statusButtons) statusButtons.style.display = 'none';
    if (typeButtons) typeButtons.style.display = 'none';
    if (houseCommitteeButtons) houseCommitteeButtons.style.display = 'none';
    if (senateCommitteeButtons) senateCommitteeButtons.style.display = 'none';
    if (jointCommitteeButtons) jointCommitteeButtons.style.display = 'none';
    if (hotBillsSection) hotBillsSection.style.display = 'none';
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
    loadHotBills(sessionKey);
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
    
    // Bill button click handlers (set up once on page load)
    document.addEventListener('click', function(e) {
        if (e.target.closest('.bill-button')) {
            e.preventDefault();
            const button = e.target.closest('.bill-button');
            const filterType = button.getAttribute('data-filter-type');
            const filterValue = button.getAttribute('data-filter-value');
            
            // Placeholder for navigation - will be implemented later
            console.log(`🔍 Navigate to ${filterType}: ${filterValue}`);
            
            // Show user feedback
            showAlert('info', 'Navigation Coming Soon', 
                `You clicked on "${button.querySelector('.bill-label').textContent}". ` +
                `Bill listing pages will be implemented in the next phase.`);
            
            // Add visual feedback
            button.style.transform = 'scale(0.95)';
            setTimeout(() => {
                button.style.transform = '';
            }, 150);
        }
    });
    
    // Load initial data
    loadSessions();
});

// Bill Type Information Helper
function getBillTypeInfo(prefix) {
    const billTypes = {
        'HB': { name: 'House Bill', description: 'Legislation originating in the House' },
        'SB': { name: 'Senate Bill', description: 'Legislation originating in the Senate' },
        'HCR': { name: 'House Concurrent Resolution', description: 'House resolution requiring Senate agreement' },
        'SCR': { name: 'Senate Concurrent Resolution', description: 'Senate resolution requiring House agreement' },
        'HR': { name: 'House Resolution', description: 'House-only resolution' },
        'SR': { name: 'Senate Resolution', description: 'Senate-only resolution' },
        'HJR': { name: 'House Joint Resolution', description: 'Constitutional amendment from House' },
        'SJR': { name: 'Senate Joint Resolution', description: 'Constitutional amendment from Senate' },
        'HJM': { name: 'House Joint Memorial', description: 'House memorial to federal government' },
        'SJM': { name: 'Senate Joint Memorial', description: 'Senate memorial to federal government' }
    };
    
    return billTypes[prefix] || { name: `${prefix}`, description: `Unknown bill type: ${prefix}` };
}

// Export functions for potential external use
window.OLIS = {
    loadSessions,
    loadSessionStats,
    selectSession,
    updateConnectionStatus,
    showAlert,
    hideAlert
};