/**
 * Application Dashboard JavaScript
 * EXAMPLE: This implements task management functionality to demonstrate patterns.
 * Replace the task-related functions with your own application logic.
 * KEEP the patterns: async/await, error handling, UI updates, Storage integration.
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// State
let refreshInterval = null;
let startTime = Date.now();
let connectionStatus = 'connected'; // connected, disconnected, reconnecting
let errorCount = 0;
let lastErrorTime = null;

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
    /* Enhanced API request with retry logic and proper error handling */
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
    
    const requestOptions = {
        signal: controller.signal,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };
    
    let lastError = null;
    const maxRetries = 3;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            updateConnectionStatus('connected');
            
            const response = await fetch(url, requestOptions);
            clearTimeout(timeoutId);
            
            // Reset error count on successful request
            errorCount = 0;
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new ApiError(
                    errorData.error?.message || `HTTP ${response.status}`,
                    errorData.error?.code || 'HTTP_ERROR',
                    response.status,
                    errorData.error?.details
                );
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            clearTimeout(timeoutId);
            lastError = error;
            
            if (error.name === 'AbortError') {
                updateConnectionStatus('disconnected');
                throw new ApiError('Request timeout - check your connection', 'TIMEOUT', 408);
            }
            
            if (error instanceof ApiError) {
                throw error;
            }
            
            // Network error - likely server down
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                updateConnectionStatus('disconnected');
                
                if (attempt < maxRetries) {
                    updateConnectionStatus('reconnecting');
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt)); // Exponential backoff
                    continue;
                }
                
                throw new ApiError('Unable to connect to server', 'NETWORK_ERROR', 0);
            }
            
            throw error;
        }
    }
    
    throw lastError;
}

function updateConnectionStatus(status) {
    /* Update connection status indicator */
    connectionStatus = status;
    
    const statusDot = document.querySelector('.status-dot');
    const statusBadge = document.querySelector('.badge-success');
    
    if (statusDot && statusBadge) {
        statusDot.className = 'status-dot';
        
        switch (status) {
            case 'connected':
                statusDot.classList.add('running');
                statusBadge.className = 'badge badge-success';
                statusBadge.textContent = 'Connected';
                break;
            case 'disconnected':
                statusDot.classList.add('stopped');
                statusBadge.className = 'badge badge-danger';
                statusBadge.textContent = 'Disconnected';
                break;
            case 'reconnecting':
                statusDot.classList.add('pending');
                statusBadge.className = 'badge badge-warning';
                statusBadge.textContent = 'Reconnecting...';
                break;
        }
    }
}

function handleError(error, context = 'operation') {
    /* Centralized error handling with logging and user feedback */
    errorCount++;
    lastErrorTime = Date.now();
    
    console.error(`Error in ${context}:`, error);
    
    let message = 'An unexpected error occurred';
    let type = 'danger';
    
    if (error instanceof ApiError) {
        switch (error.code) {
            case 'NETWORK_ERROR':
                message = 'Unable to connect to server. Please check your internet connection.';
                type = 'warning';
                break;
            case 'TIMEOUT':
                message = 'Request timed out. Please try again.';
                type = 'warning';
                break;
            case 'VALIDATION_ERROR':
                message = error.details || error.message;
                type = 'warning';
                break;
            case 'RESOURCE_NOT_FOUND':
                message = error.message;
                type = 'info';
                break;
            case 'UNAUTHORIZED':
                message = 'You are not authorized to perform this action.';
                type = 'danger';
                break;
            default:
                message = error.message;
                type = 'danger';
        }
    } else {
        message = error.message || 'An unexpected error occurred';
    }
    
    showAlert(`${context}: ${message}`, type);
    
    // Update connection status if needed
    if (error instanceof ApiError && (error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT')) {
        updateConnectionStatus('disconnected');
    }
}

function showLoadingState(elementId, isLoading = true) {
    /* Show/hide loading state for elements */
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (isLoading) {
        element.style.opacity = '0.6';
        element.style.pointerEvents = 'none';
        
        // Add spinner if not already present
        if (!element.querySelector('.loading-spinner')) {
            const spinner = document.createElement('div');
            spinner.className = 'loading-spinner';
            spinner.innerHTML = '<div class="spinner"></div>';
            spinner.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);';
            element.style.position = 'relative';
            element.appendChild(spinner);
        }
    } else {
        element.style.opacity = '1';
        element.style.pointerEvents = 'auto';
        
        // Remove spinner
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

async function reportErrorToBackend(errorInfo) {
    /* Report frontend errors to backend for monitoring */
    try {
        // Only report if we're connected
        if (connectionStatus === 'disconnected') return;
        
        const errorData = {
            ...errorInfo,
            userAgent: navigator.userAgent,
            url: window.location.href,
            timestamp: new Date().toISOString()
        };
        
        // Use basic fetch to avoid our enhanced error handling (prevent recursion)
        await fetch(`${API_BASE_URL}/debug/report-error`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(errorData)
        });
        
    } catch (error) {
        // Silently fail - don't want error reporting to cause more errors
        console.debug('Failed to report error to backend:', error.message);
    }
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Starter Template Dashboard initialized');
    updateUptime();
    refreshStatus();
    
    // Detect page type and initialize accordingly
    const taskForm = document.getElementById('task-form');
    const healthMetrics = document.getElementById('system-uptime');
    const isDemo = taskForm !== null;
    const isHealth = healthMetrics !== null;
    
    if (isDemo) {
        console.log('Loading demo functionality...');
        loadTasks();
        loadActivity();
        taskForm.addEventListener('submit', createTask);
        
        // Set up auto-refresh for demo page
        refreshInterval = setInterval(() => {
            updateUptime();
            refreshStatus();
            loadTasks();
        }, 10000);
    } else if (isHealth) {
        console.log('Loading health page functionality...');
        loadHealthMetrics();
        loadErrorStats();
        
        // Set up auto-refresh for health page
        refreshInterval = setInterval(() => {
            updateHealthUptime();
            loadHealthMetrics();
            loadErrorStats();
        }, 15000); // Refresh every 15 seconds for health monitoring
    } else {
        console.log('Home page loaded');
        // Set up lighter refresh for home page (just status)
        refreshInterval = setInterval(() => {
            updateUptime();
            refreshStatus();
        }, 30000); // Less frequent for home page
    }
    
    // Set up connection health monitoring
    setInterval(checkConnectionHealth, 30000); // Check every 30 seconds
});

// Connection Health Monitoring
async function checkConnectionHealth() {
    /* Periodic connection health check */
    if (connectionStatus === 'disconnected') {
        try {
            await makeApiRequest(`${API_BASE_URL}/health`);
            console.log('Connection restored');
            showAlert('Connection restored', 'success');
        } catch (error) {
            // Still disconnected, no need to spam alerts
            console.log('Still disconnected:', error.message);
        }
    }
}

// Update uptime display
function updateUptime() {
    const now = Date.now();
    const diff = now - startTime;
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    const uptimeEl = document.getElementById('uptime');
    if (uptimeEl) {
        uptimeEl.textContent = `${days}d ${hours}h ${minutes}m`;
    }
}

// Refresh status from API
async function refreshStatus() {
    try {
        showLoadingState('metric-total', true);
        
        const data = await makeApiRequest(`${API_BASE_URL}/status`);
        
        // Update last check time
        const lastCheckEl = document.getElementById('last-check');
        if (lastCheckEl) {
            lastCheckEl.textContent = new Date().toLocaleTimeString();
        }
        
        // Handle both direct response and success wrapper
        const responseData = data.success ? data.data : data;
        
        // Check if we're on demo page (has task functionality)
        const isDemo = document.getElementById('task-form') !== null;
        
        if (isDemo) {
            // Update metrics if they exist - for demo page, show task-specific metrics
            if (responseData.task_counts) {
                updateMetric('metric-total', responseData.task_counts.total);
                updateMetric('metric-completed', responseData.task_counts.completed);
                updateMetric('metric-pending', responseData.task_counts.pending + responseData.task_counts.in_progress);
            } else if (responseData.metrics) {
                // Fallback to generic metrics for demo page
                updateMetric('metric-completed', responseData.metrics.processed);
                updateMetric('metric-pending', responseData.metrics.pending);
            }
        } else {
            // Home page - show template status instead of counts
            updateMetric('metric-total', 'Running');
            updateMetric('metric-completed', 'Ready'); 
            updateMetric('metric-pending', 'Loaded');
        }
        
        console.log('Status refreshed:', data);
    } catch (error) {
        handleError(error, 'Status refresh');
    } finally {
        showLoadingState('metric-total', false);
    }
}

// Update a metric display
function updateMetric(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        const currentValue = parseInt(element.textContent);
        if (currentValue !== value) {
            element.textContent = value;
            // Add a brief highlight animation
            element.style.color = 'var(--primary)';
            setTimeout(() => {
                element.style.color = '';
            }, 500);
        }
    }
}

// Legacy action function - creates a sample task
async function performAction() {
    console.log('Creating sample task...');
    
    // Disable button temporarily
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Creating...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                timestamp: new Date().toISOString(),
                source: 'dashboard'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Sample task created successfully', 'success');
            // Refresh data
            refreshStatus();
            loadTasks();
            loadActivity();
        } else {
            showAlert('Action failed: ' + data.error, 'danger');
        }
        
    } catch (error) {
        console.error('Action failed:', error);
        showAlert('Failed to perform action', 'danger');
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Run Action';
    }
}

// Health Page Functions - Real system monitoring
// -------------------------

// Update uptime for health page
function updateHealthUptime() {
    const now = Date.now();
    const diff = now - startTime;
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    const uptimeEl = document.getElementById('system-uptime');
    if (uptimeEl) {
        uptimeEl.textContent = `${days}d ${hours}h ${minutes}m`;
    }
}

// Load comprehensive health metrics
async function loadHealthMetrics() {
    try {
        const startTime = Date.now();
        const data = await makeApiRequest(`${API_BASE_URL}/status`);
        const responseTime = Date.now() - startTime;
        
        // Update last check time
        const lastCheckEl = document.getElementById('last-health-check');
        if (lastCheckEl) {
            lastCheckEl.textContent = new Date().toLocaleTimeString();
        }
        
        // Handle both direct response and success wrapper
        const systemData = data.success ? data.data : data;
        
        // Update system health indicators
        if (systemData.system_health) {
            const health = systemData.system_health;
            
            // FastAPI Status
            updateHealthMetric('fastapi-status', health.fastapi_status || 'Running');
            
            // Database Status
            const dbStatus = health.database_healthy ? 'Connected' : 'Error';
            updateHealthMetric('database-status', dbStatus);
            if (!health.database_healthy && health.database_error) {
                console.error('Database error:', health.database_error);
            }
            
            // Memory Usage
            updateHealthMetric('memory-usage', `${health.memory_usage_mb || 0} MB`);
            
            // Schema Version
            updateHealthMetric('schema-version', health.schema_version || 'Unknown');
            
            // Storage stats
            if (systemData.database_stats && systemData.database_stats.total_records) {
                updateHealthMetric('storage-used', `${systemData.database_stats.total_records} records`);
            }
        }
        
        // Update performance metrics
        updateHealthMetric('response-time', `${responseTime}ms`);
        
        // Update error rate from error_stats
        if (systemData.error_stats) {
            updateHealthMetric('error-rate', `${systemData.error_stats.errors_last_hour || 0}/hour`);
        }
        
        // Update app name in UI
        if (systemData.config && systemData.config.app_name) {
            const appName = systemData.config.app_name;
            const brandLink = document.getElementById('app-brand-link');
            const appNameDisplay = document.getElementById('app-name-display');
            
            if (brandLink) brandLink.textContent = appName;
            if (appNameDisplay) appNameDisplay.textContent = appName.toLowerCase();
        }
        
        // Update configuration info
        if (systemData.config) {
            const config = systemData.config;
            updateHealthMetric('environment', config.environment || 'Unknown');
            updateHealthMetric('debug-mode', config.debug_mode ? 'Enabled' : 'Disabled');
            updateHealthMetric('server-port', config.port || 8000);
            updateHealthMetric('database-path', config.database_path || 'Unknown');
        }
        
        // Update system info from system_health
        if (systemData.system_health) {
            const health = systemData.system_health;
            updateHealthMetric('python-version', health.python_version || 'Unknown');
            updateHealthMetric('platform-info', health.platform || 'Unknown');
            updateHealthMetric('restart-count', health.restart_count || 0);
            updateHealthMetric('last-restart', health.last_restart ? 
                new Date(health.last_restart).toLocaleString() : 'Never');
        }
        
        // Update service status indicator
        const statusDot = document.getElementById('service-status-dot');
        const statusBadge = document.getElementById('service-status-badge');
        
        if (statusDot && statusBadge) {
            if (systemData.status === 'running') {
                statusDot.className = 'status-dot running';
                statusBadge.className = 'badge badge-success';
                statusBadge.textContent = 'Service Running';
            } else if (systemData.status === 'degraded') {
                statusDot.className = 'status-dot pending';
                statusBadge.className = 'badge badge-warning';
                statusBadge.textContent = 'Service Degraded';
            } else {
                statusDot.className = 'status-dot stopped';
                statusBadge.className = 'badge badge-danger';
                statusBadge.textContent = 'Service Error';
            }
        }
        
        // Update uptime display
        if (systemData.uptime) {
            const systemUptimeEl = document.getElementById('system-uptime');
            if (systemUptimeEl) {
                systemUptimeEl.textContent = systemData.uptime;
            }
        }
        
        console.log('Health metrics updated:', systemData);
    } catch (error) {
        handleError(error, 'Load health metrics');
    }
}

// Load error statistics
async function loadErrorStats() {
    try {
        const data = await makeApiRequest(`${API_BASE_URL}/debug/error-stats`);
        
        // Handle both direct response and success wrapper  
        const errorData = data.success ? data.data : data;
        
        // Update error metrics
        updateHealthMetric('errors-last-hour', errorData.error_rate_per_hour || 0);
        updateHealthMetric('total-errors', errorData.total_errors || 0);
        updateHealthMetric('frontend-errors', errorData.frontend_errors || 0);
        
        // Update last error time
        if (errorData.recent_error_logs && errorData.recent_error_logs.length > 0) {
            const lastError = errorData.recent_error_logs[0];
            const errorTime = lastError.created_at ? new Date(lastError.created_at).toLocaleString() : 'Unknown';
            updateHealthMetric('last-error-time', errorTime);
        } else {
            updateHealthMetric('last-error-time', 'None');
        }
        
        // Display recent errors
        const errorsList = document.getElementById('recent-errors-list');
        if (errorsList && errorData.recent_error_logs) {
            if (errorData.recent_error_logs.length === 0) {
                errorsList.innerHTML = '<p class="text-secondary">No recent errors</p>';
            } else {
                errorsList.innerHTML = errorData.recent_error_logs.slice(0, 5).map(error => {
                    const errorTime = error.created_at ? new Date(error.created_at).toLocaleString() : 'Unknown time';
                    return `
                        <div class="error-item" style="padding: var(--space-2) 0; border-bottom: 1px solid var(--border);">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="badge badge-danger">Error</span>
                                    <span style="margin-left: var(--space-2); font-size: var(--text-sm);">${error.message || 'Unknown error'}</span>
                                </div>
                                <span class="text-small text-secondary">${errorTime}</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
        
        console.log('Error stats updated:', errorData);
    } catch (error) {
        handleError(error, 'Load error statistics');
        // Set fallback values
        updateHealthMetric('errors-last-hour', 'Error');
        updateHealthMetric('total-errors', 'Error');
        updateHealthMetric('frontend-errors', 'Error');
        updateHealthMetric('last-error-time', 'Error');
    }
}

// Refresh health metrics (button handler)
async function refreshHealthMetrics() {
    console.log('Manually refreshing health metrics...');
    await loadHealthMetrics();
    await loadErrorStats();
    showAlert('Health metrics refreshed', 'info');
}

// Update a health metric display
function updateHealthMetric(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        if (element.textContent !== value.toString()) {
            element.textContent = value;
            // Add a brief highlight animation
            element.style.color = 'var(--primary)';
            setTimeout(() => {
                element.style.color = '';
            }, 500);
        }
    }
}

// EXAMPLE: Task Management Functions - Replace with your application logic
// KEEP these patterns: proper error handling, UI feedback, Storage integration
// -------------------------

// Create new task
async function createTask(event) {
    event.preventDefault();
    
    const titleInput = document.getElementById('task-title');
    const descriptionInput = document.getElementById('task-description');
    const prioritySelect = document.getElementById('task-priority');
    const submitButton = event.target.querySelector('button[type="submit"]');
    
    // Client-side validation
    if (!titleInput.value.trim()) {
        showAlert('Task title is required', 'warning');
        titleInput.focus();
        return;
    }
    
    const taskData = {
        title: titleInput.value.trim(),
        description: descriptionInput.value.trim() || null,
        priority: prioritySelect.value
    };
    
    try {
        // Show loading state with spinner
        showLoadingState('task-form', true);
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner"></span> Creating...';
        
        const result = await makeApiRequest(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
        
        // Handle standardized response format
        const taskData = result.success ? result.data.task : result;
        const taskTitle = taskData.title || taskData.data?.task?.title;
        
        // Show success state
        submitButton.innerHTML = '✓ Created!';
        submitButton.style.backgroundColor = 'var(--success)';
        setTimeout(() => {
            submitButton.innerHTML = 'Create Task';
            submitButton.style.backgroundColor = '';
        }, 2000);
        
        showAlert(`Task "${taskTitle}" created successfully!`, 'success');
        
        // Clear form
        titleInput.value = '';
        descriptionInput.value = '';
        prioritySelect.value = 'medium';
        
        // Refresh data
        refreshStatus();
        loadTasks();
        loadActivity();
        
    } catch (error) {
        handleError(error, 'Create task');
        
        // Keep form data on error so user doesn't lose their input
        titleInput.focus();
    } finally {
        showLoadingState('task-form', false);
        submitButton.disabled = false;
        // Don't reset button text here - let success state handle it
        if (!submitButton.innerHTML.includes('✓')) {
            submitButton.innerHTML = 'Create Task';
        }
    }
}

// Load and display tasks
async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks`);
        const tasks = await response.json();
        
        const tasksList = document.getElementById('tasks-list');
        
        if (tasks.length === 0) {
            tasksList.innerHTML = `
                <div class="empty-state">
                    <p style="font-size: var(--text-lg); margin-bottom: var(--space-2);">
                        No tasks yet
                    </p>
                    <p class="text-secondary">
                        Create your first task using the form above ↑
                    </p>
                </div>
            `;
            return;
        }
        
        tasksList.innerHTML = tasks.map(task => {
            const statusBadge = getStatusBadge(task.status);
            const priorityBadge = getPriorityBadge(task.priority);
            const createdDate = new Date(task.created_at).toLocaleDateString();
            
            return `
                <div class="task-item" style="padding: var(--space-4); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: var(--space-3); background: var(--bg);">
                    <div class="flex items-center justify-between" style="margin-bottom: var(--space-2);">
                        <div class="flex items-center gap-2">
                            <h4 style="margin: 0; font-size: var(--text-base);">${task.title}</h4>
                            ${priorityBadge}
                        </div>
                        <div class="flex items-center gap-2">
                            ${statusBadge}
                            <select class="form-select" style="width: auto; font-size: var(--text-xs); padding: var(--space-1) var(--space-2);" onchange="updateTaskStatus(${task.id}, this.value)">
                                <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>Pending</option>
                                <option value="in_progress" ${task.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                                <option value="completed" ${task.status === 'completed' ? 'selected' : ''}>Completed</option>
                            </select>
                            <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">Delete</button>
                        </div>
                    </div>
                    ${task.description ? `<p style="margin: 0; color: var(--text-secondary); font-size: var(--text-sm);">${task.description}</p>` : ''}
                    <p style="margin: var(--space-2) 0 0 0; font-size: var(--text-xs); color: var(--text-tertiary);">Created: ${createdDate}</p>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Failed to load tasks:', error);
        showAlert('Failed to load tasks', 'danger');
    }
}

// Update task status
async function updateTaskStatus(taskId, newStatus) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: newStatus })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(`Task status updated to ${newStatus}`, 'success');
            refreshStatus();
            loadTasks();
            loadActivity();
        } else {
            throw new Error(result.detail || 'Failed to update task');
        }
    } catch (error) {
        console.error('Failed to update task:', error);
        showAlert('Failed to update task: ' + error.message, 'danger');
        loadTasks(); // Reload to reset the select
    }
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Task deleted successfully', 'success');
            refreshStatus();
            loadTasks();
            loadActivity();
        } else {
            throw new Error(result.detail || 'Failed to delete task');
        }
    } catch (error) {
        console.error('Failed to delete task:', error);
        showAlert('Failed to delete task: ' + error.message, 'danger');
    }
}

// Load recent activity - KEEP THIS PATTERN for activity tracking in any app
async function loadActivity() {
    try {
        const response = await fetch(`${API_BASE_URL}/activity`);
        const data = await response.json();
        
        const activityList = document.getElementById('activity-list');
        
        if (!data.events || data.events.length === 0) {
            activityList.innerHTML = '<p class="text-secondary">No recent activity</p>';
            return;
        }
        
        activityList.innerHTML = data.events.map(event => {
            const eventDate = new Date(event.created_at).toLocaleString();
            const eventData = event.data || {};
            
            let eventText = event.event_type;
            if (eventData.title) {
                eventText += `: ${eventData.title}`;
            }
            if (eventData.old_status && eventData.new_status) {
                eventText = `Task status changed from ${eventData.old_status} to ${eventData.new_status}`;
                if (eventData.title) eventText += ` (${eventData.title})`;
            }
            
            const badge = getEventBadge(event.event_type);
            
            return `
                <div class="activity-item" style="padding: var(--space-2) 0; border-bottom: 1px solid var(--border);">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            ${badge}
                            <span style="font-size: var(--text-sm);">${eventText}</span>
                        </div>
                        <span class="text-small text-secondary">${eventDate}</span>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Failed to load activity:', error);
    }
}

// View activity (alias for loadActivity)
function viewActivity() {
    loadActivity();
}


// Helper functions
function getStatusBadge(status) {
    const badges = {
        'pending': 'badge-warning',
        'in_progress': 'badge-info', 
        'completed': 'badge-success'
    };
    return `<span class="badge ${badges[status] || 'badge-default'}">${status.replace('_', ' ')}</span>`;
}

function getPriorityBadge(priority) {
    const badges = {
        'low': 'badge-default',
        'medium': 'badge-info',
        'high': 'badge-danger'
    };
    return `<span class="badge ${badges[priority] || 'badge-default'}">${priority}</span>`;
}

function getEventBadge(eventType) {
    const badges = {
        'task_created': 'badge-success',
        'task_status_changed': 'badge-info',
        'task_deleted': 'badge-danger'
    };
    return `<span class="badge ${badges[eventType] || 'badge-default'}">${eventType.replace('_', ' ')}</span>`;
}

// Add activity to the list
function addActivity(message, type = 'default') {
    const activityList = document.getElementById('activity-list');
    
    // Remove "no activity" message if it exists
    if (activityList.querySelector('.text-secondary')) {
        activityList.innerHTML = '';
    }
    
    // Create new activity item
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    activityItem.style.cssText = 'padding: var(--space-2) 0; border-bottom: 1px solid var(--border);';
    
    const badge = getBadgeClass(type);
    const time = new Date().toLocaleTimeString();
    
    activityItem.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
                <span class="badge ${badge}">${type}</span>
                <span>${message}</span>
            </div>
            <span class="text-small text-secondary">${time}</span>
        </div>
    `;
    
    // Add to top of list
    activityList.insertBefore(activityItem, activityList.firstChild);
    
    // Keep only last 10 items
    while (activityList.children.length > 10) {
        activityList.removeChild(activityList.lastChild);
    }
}

// Clear activity list
function clearActivity() {
    const activityList = document.getElementById('activity-list');
    activityList.innerHTML = '<p class="text-secondary">No recent activity</p>';
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    alertContainer.style.display = 'block';
    
    const alertClass = `alert-${type}`;
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass}`;
    alert.innerHTML = `
        <div class="alert-content">
            <div class="alert-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div>${message}</div>
        </div>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.remove();
        if (alertContainer.children.length === 0) {
            alertContainer.style.display = 'none';
        }
    }, 5000);
}

// Get badge class for activity type
function getBadgeClass(type) {
    const badgeMap = {
        'success': 'badge-success',
        'warning': 'badge-warning',
        'danger': 'badge-danger',
        'info': 'badge-info',
        'default': 'badge-default'
    };
    return badgeMap[type] || 'badge-default';
}

// Enhanced Global Error Handling
window.addEventListener('error', (event) => {
    console.error('Global JavaScript error:', event.error);
    
    // Don't spam alerts for script errors
    if (Date.now() - lastErrorTime < 5000) return;
    
    errorCount++;
    lastErrorTime = Date.now();
    
    // Log error details for debugging
    const errorInfo = {
        message: event.error?.message || event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString()
    };
    
    console.error('Error details:', errorInfo);
    
    // Report error to backend (fire and forget)
    reportErrorToBackend(errorInfo).catch(() => {
        // Ignore reporting failures to avoid recursion
    });
    
    showAlert(`JavaScript error occurred. Check console for details.`, 'danger');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Don't spam alerts
    if (Date.now() - lastErrorTime < 5000) return;
    
    errorCount++;
    lastErrorTime = Date.now();
    
    let message = 'An unexpected error occurred';
    
    if (event.reason instanceof ApiError) {
        handleError(event.reason, 'Unhandled operation');
        return; // handleError will show the alert
    } else if (event.reason?.message) {
        message = `Operation failed: ${event.reason.message}`;
    }
    
    showAlert(message, 'danger');
    
    // Prevent the default unhandled rejection handling
    event.preventDefault();
});

// Monitor for offline/online status
window.addEventListener('offline', () => {
    console.log('Network connection lost');
    updateConnectionStatus('disconnected');
    showAlert('Network connection lost. Trying to reconnect...', 'warning');
});

window.addEventListener('online', () => {
    console.log('Network connection restored');
    showAlert('Network connection restored', 'success');
    // Trigger a status check to confirm server connectivity
    setTimeout(refreshStatus, 1000);
});

// Add visibility change handling (tab switching)
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && connectionStatus === 'disconnected') {
        // Tab became visible and we're disconnected - try to reconnect
        setTimeout(checkConnectionHealth, 500);
    }
});

// Enhanced cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Log final error statistics
    if (errorCount > 0) {
        console.log(`Session ended with ${errorCount} errors`);
    }
});

// Performance monitoring (basic)
if ('performance' in window && 'getEntriesByType' in performance) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation && navigation.loadEventEnd > 5000) {
                console.warn(`Slow page load: ${Math.round(navigation.loadEventEnd)}ms`);
            }
        }, 0);
    });
}
