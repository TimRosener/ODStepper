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
let currentPage = '/'; // Track current page

// Navigation State
const pages = {
    '/': 'main-dashboard',
    '/bill-status': 'bill-status-dashboard', 
    '/bill-types': 'bill-types-dashboard',
    '/house-committees': 'house-committees-dashboard',
    '/senate-committees': 'senate-committees-dashboard', 
    '/joint-committees': 'joint-committees-dashboard'
};

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
    // Store current stats for navigation
    currentStats = stats;
    
    // Update total bills count
    const totalCount = document.getElementById('total-bills-count');
    if (totalCount) {
        totalCount.textContent = stats.total_bills || 0;
    }
    
    // Hide loading
    const dashboardLoading = document.getElementById('dashboard-loading');
    if (dashboardLoading) dashboardLoading.style.display = 'none';
    
    // Navigate to current page to show appropriate content
    navigateToPage(currentPage, false);
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
    
    // Generate hot bill buttons with expandable details
    if (hotBillsGrid) {
        const hotBillButtons = hotBillsData.hot_bills.map((bill, index) => {
            const heatClass = `heat-${bill.heat_level}`;
            const billId = `hot-bill-${index}`;
            
            // Position breakdown data
            const positions = bill.position_breakdown || {};
            const inFavor = positions.in_favor || 0;
            const against = positions.against || 0;
            const neutral = positions.neutral || 0;
            const unknown = positions.unknown || 0;
            
            // Submitter type data
            const submitterTypes = bill.submitter_types || {};
            const organizations = submitterTypes.organizations || 0;
            const individuals = submitterTypes.individuals || 0;
            
            return `
                <div class="hot-bill-container">
                    <button class="bill-button hot-bill-button ${heatClass}" 
                            data-filter-type="hot-bill" 
                            data-filter-value="${bill.bill_id}"
                            title="${bill.title}">
                        <div class="hot-bill-header">
                            <span class="heat-indicator">${bill.heat_emoji}</span>
                        </div>
                        <span class="bill-label">${bill.bill_id}</span>
                        <div class="bill-title" title="${bill.title}">${bill.title}</div>
                        
                        <!-- Position Breakdown Summary -->
                        <div class="position-summary">
                            <span class="position-item in-favor" title="In Favor">👍 ${inFavor}</span>
                            <span class="position-item against" title="Against">👎 ${against}</span>
                            <span class="position-item neutral" title="Neutral">⚖️ ${neutral}</span>
                            <span class="position-item unknown" title="Unknown">❓ ${unknown}</span>
                        </div>
                        
                        <div class="hotness-score" title="Hotness Score: ${bill.hotness_score}">
                            Score: ${bill.hotness_score}
                        </div>
                    </button>
                    
                    <!-- Expandable Details Toggle -->
                    <button class="details-toggle" data-bill-id="${billId}" title="Show/Hide Details">
                        <span class="toggle-icon">▼</span> Details
                    </button>
                    
                    <!-- Expandable Details Panel -->
                    <div class="bill-details" id="${billId}-details" style="display: none;">
                        <div class="details-grid">
                            <div class="detail-section">
                                <h4>Submitter Types</h4>
                                <ul class="submitter-details">
                                    <li>🏢 Organizations: <strong>${organizations}</strong></li>
                                    <li>👤 Individuals: <strong>${individuals}</strong></li>
                                    <li>🏛️ Government: <strong>${submitterTypes.government || 0}</strong></li>
                                    <li>💼 Business: <strong>${submitterTypes.business || 0}</strong></li>
                                    <li>🤝 Nonprofit: <strong>${submitterTypes.nonprofit || 0}</strong></li>
                                </ul>
                            </div>
                            
                            <div class="detail-section">
                                <h4>Timeline Analysis</h4>
                                <ul class="timeline-details">
                                    <li>📅 Last 30 days: <strong>${bill.timeline_breakdown?.recent_30_days || 0}</strong></li>
                                    <li>📊 Last 90 days: <strong>${bill.timeline_breakdown?.recent_90_days || 0}</strong></li>
                                    <li>🗓️ This year: <strong>${bill.timeline_breakdown?.this_year || 0}</strong></li>
                                    <li>📜 Older: <strong>${bill.timeline_breakdown?.older || 0}</strong></li>
                                </ul>
                            </div>
                            
                            <div class="detail-section">
                                <h4>🏙️ Top 10 Cities/Locations</h4>
                                <ol class="top-submitters-list">
                                    ${(bill.top_submitters || []).map((submitter, index) => 
                                        `<li>${submitter.emoji} <strong>${submitter.name}</strong> (${submitter.count} ${submitter.count === 1 ? 'testimony' : 'testimonies'})</li>`
                                    ).join('')}
                                </ol>
                                ${!bill.top_submitters || bill.top_submitters.length === 0 ? 
                                    '<p class="no-data">No city/location data available</p>' : ''}
                            </div>
                            
                            <div class="detail-section">
                                <h4>🏛️ Top 10 On Behalf Of</h4>
                                <ol class="top-behalf-of-list">
                                    ${(bill.top_behalf_of || []).map((behalf, index) => 
                                        `<li>${behalf.emoji} <strong>${behalf.name}</strong> (${behalf.count} ${behalf.count === 1 ? 'testimony' : 'testimonies'})</li>`
                                    ).join('')}
                                </ol>
                                ${!bill.top_behalf_of || bill.top_behalf_of.length === 0 ? 
                                    '<p class="no-data">No organization representation data available</p>' : ''}
                            </div>
                        </div>
                    </div>
                </div>`;
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

function toggleBillDetails(billId) {
    const detailsPanel = document.getElementById(billId + '-details');
    const toggleButton = document.querySelector(`button.details-toggle[data-bill-id="${billId}"]`);
    const toggleIcon = toggleButton?.querySelector('.toggle-icon');
    
    if (detailsPanel) {
        const isVisible = detailsPanel.style.display !== 'none';
        
        if (isVisible) {
            // Hide details
            detailsPanel.style.display = 'none';
            if (toggleIcon) toggleIcon.textContent = '▼';
            if (toggleButton) toggleButton.title = 'Show Details';
        } else {
            // Show details
            detailsPanel.style.display = 'block';
            if (toggleIcon) toggleIcon.textContent = '▲';
            if (toggleButton) toggleButton.title = 'Hide Details';
        }
    }
}

// Navigation Functions
function navigateToPage(path, updateHistory = true) {
    // Update current page
    currentPage = path;
    
    // Hide all dashboards
    const allDashboards = document.querySelectorAll('.card');
    allDashboards.forEach(dashboard => {
        if (dashboard.id !== 'main-dashboard' && dashboard.classList.contains('category-dashboard')) {
            dashboard.style.display = 'none';
        }
    });
    
    // Show main dashboard by default
    const mainDashboard = document.getElementById('main-dashboard');
    if (mainDashboard) {
        mainDashboard.style.display = path === '/' ? 'block' : 'none';
    }
    
    // Show specific category dashboard if needed
    const targetDashboardId = pages[path];
    if (targetDashboardId && targetDashboardId !== 'main-dashboard') {
        const targetDashboard = document.getElementById(targetDashboardId);
        if (targetDashboard) {
            targetDashboard.style.display = 'block';
        }
    }
    
    // Update sidebar navigation
    updateSidebarNavigation(path);
    
    // Show/hide submenu based on page
    const submenu = document.getElementById('session-submenu');
    const sessionOverviewMain = document.getElementById('session-overview-main');
    
    if (path === '/' || Object.keys(pages).includes(path)) {
        // Show submenu for session-related pages
        if (submenu) submenu.style.display = 'block';
        if (sessionOverviewMain) sessionOverviewMain.classList.add('expanded');
    } else {
        // Hide submenu for external pages
        if (submenu) submenu.style.display = 'none';
        if (sessionOverviewMain) sessionOverviewMain.classList.remove('expanded');
    }
    
    // Update browser history
    if (updateHistory && path !== window.location.pathname) {
        history.pushState({ path }, '', path);
    }
    
    // Show appropriate content based on current session
    if (currentSession && currentStats) {
        if (path === '/') {
            showSessionOverview();
        } else {
            showCategoryContent(path);
        }
    }
}

function updateSidebarNavigation(currentPath) {
    // Update main links
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Update sublinks
    document.querySelectorAll('.sidebar-sublink').forEach(link => {
        link.classList.remove('active');
    });
    
    if (currentPath === '/') {
        const sessionLink = document.getElementById('session-overview-main');
        if (sessionLink) sessionLink.classList.add('active');
    } else {
        // First, try to find and activate the appropriate sublink (bill-status, bill-types, etc.)
        const targetSublink = document.querySelector(`a[href="${currentPath}"].sidebar-sublink`);
        if (targetSublink) {
            targetSublink.classList.add('active');
            // Keep session overview main link active too
            const sessionLink = document.getElementById('session-overview-main');
            if (sessionLink) sessionLink.classList.add('active');
        } else {
            // If no sublink found, try to find main sidebar link (system-health, examples)
            const targetMainLink = document.querySelector(`a[href="${currentPath}"].sidebar-link`);
            if (targetMainLink) {
                targetMainLink.classList.add('active');
            }
        }
    }
}

function showSessionOverview() {
    // Show hot bills on main overview
    if (currentHotBills) {
        displayHotBills(currentHotBills);
    }
}

function showCategoryContent(path) {
    if (!currentStats) return;
    
    // Hide hot bills on category pages  
    hideHotBills();
    
    // Show specific category content
    switch (path) {
        case '/bill-status':
            if (currentStats.status_display) {
                populateStatusButtons(currentStats.status_display);
                showElement('status-buttons');
            }
            break;
        case '/bill-types':
            if (currentStats.bill_type_counts) {
                populateTypeButtons(currentStats.bill_type_counts, currentStats.total_bills);
                showElement('type-buttons');
            }
            break;
        case '/house-committees':
            if (currentStats.specific_committees?.house_committees) {
                populateCommitteeButtons('house', currentStats.specific_committees.house_committees);
                showElement('house-committee-buttons');
            }
            break;
        case '/senate-committees':
            if (currentStats.specific_committees?.senate_committees) {
                populateCommitteeButtons('senate', currentStats.specific_committees.senate_committees);
                showElement('senate-committee-buttons');
            }
            break;
        case '/joint-committees':
            if (currentStats.specific_committees?.joint_committees) {
                populateCommitteeButtons('joint', currentStats.specific_committees.joint_committees);
                showElement('joint-committee-buttons');
            }
            break;
    }
}

function showElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

// Helper functions for populating category content
function populateStatusButtons(statusDisplay) {
    const statusGrid = document.getElementById('status-grid');
    if (statusGrid) {
        const sortedStatuses = Object.entries(statusDisplay)
            .sort((a, b) => b[1].count - a[1].count);
        
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

function populateTypeButtons(billTypeCounts, totalBills) {
    const typeGrid = document.getElementById('type-grid');
    if (typeGrid) {
        const groupedTypes = groupBillTypes(billTypeCounts, totalBills);
        
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

function populateCommitteeButtons(chamber, committeeData) {
    const gridId = `${chamber}-committee-grid`;
    const grid = document.getElementById(gridId);
    
    if (grid && committeeData.committees) {
        const committees = Object.entries(committeeData.committees);
        
        const committeeButtons = committees.map(([code, info]) => `
            <button class="bill-button" 
                    data-filter-type="committee" 
                    data-filter-value="${code}"
                    title="${info.description || code}">
                <span class="bill-count">${info.count}</span>
                <span class="bill-label">${info.display_name || code}</span>
                <span class="bill-percentage">${(info.count / committeeData.total * 100).toFixed(1)}%</span>
            </button>
        `).join('');
        
        grid.innerHTML = committeeButtons;
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
    
    // Navigation click handlers
    document.addEventListener('click', function(e) {
        // Handle sidebar navigation links
        if (e.target.matches('.sidebar-link, .sidebar-sublink, .overview-link')) {
            const href = e.target.getAttribute('href');
            if (href) {
                // Check if this is an external page (not part of our SPA routing)
                const externalPages = ['/system-health', '/examples'];
                
                if (externalPages.includes(href)) {
                    // Allow normal browser navigation for external pages
                    // Don't prevent default - let the browser handle it
                    return;
                } else {
                    // Handle internal SPA navigation
                    e.preventDefault();
                    navigateToPage(href);
                }
            }
        }
        
        // Handle Session Overview main link toggle
        if (e.target.id === 'session-overview-main') {
            e.preventDefault();
            const submenu = document.getElementById('session-submenu');
            const mainLink = e.target;
            
            if (submenu.style.display === 'none' || submenu.style.display === '') {
                submenu.style.display = 'block';
                mainLink.classList.add('expanded');
            } else {
                submenu.style.display = 'none';
                mainLink.classList.remove('expanded');
            }
            
            // Navigate to main overview page
            navigateToPage('/');
            return;
        }
        
        // Handle bill button clicks
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
            
            return;
        }
        
        // Handle details toggle button clicks
        if (e.target.matches('.details-toggle, .details-toggle *')) {
            e.preventDefault();
            const button = e.target.closest('.details-toggle');
            if (button) {
                const billId = button.getAttribute('data-bill-id');
                if (billId) {
                    toggleBillDetails(billId);
                }
            }
            return;
        }
        
        // Handle hot bill button clicks
        if (e.target.closest('.hot-bill-button')) {
            e.preventDefault();
            const button = e.target.closest('.hot-bill-button');
            const billId = button.getAttribute('data-bill-id');
            
            // Placeholder for navigation - will be implemented later
            console.log(`🔥 Navigate to hot bill: ${billId}`);
            
            return;
        }
    });
    
    // Handle browser back/forward
    window.addEventListener('popstate', function(e) {
        const path = e.state?.path || window.location.pathname;
        navigateToPage(path, false);
    });
    
    
    // Initialize navigation on page load
    const initialPath = window.location.pathname;
    currentPage = initialPath;
    navigateToPage(initialPath, false);
    
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