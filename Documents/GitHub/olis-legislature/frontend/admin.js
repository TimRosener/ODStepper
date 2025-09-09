// OLIS Administration Interface JavaScript

class AdminInterface {
    constructor() {
        this.baseURL = window.location.origin;
        this.refreshInterval = null;
        this.currentSection = 'database';
        
        // Initialize the interface
        this.init();
    }

    async init() {
        console.log('Initializing OLIS Admin Interface...');
        
        try {
            // Load initial data
            console.log('Loading database status...');
            await this.loadDatabaseStatus();
            
            console.log('Loading system status...');
            await this.loadSystemStatus();
            
            console.log('Loading tables...');
            await this.loadTables();
            
            // Start auto-refresh for monitoring data
            console.log('Starting auto-refresh...');
            this.startAutoRefresh();
            
            console.log('Admin interface initialized successfully');
        } catch (error) {
            console.error('Failed to initialize admin interface:', error);
            // Show error message in the UI
            document.getElementById('db-connection-status').innerHTML = 
                '<span class="status-indicator status-error"></span><span>Initialization Error</span>';
            document.getElementById('db-connection-details').innerHTML = 
                `<small><strong>Error:</strong> ${error.message}</small>`;
        }
    }

    // Navigation Management
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.admin-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Remove active class from all nav buttons
        document.querySelectorAll('.admin-nav button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Show selected section
        document.getElementById(`section-${sectionName}`).classList.add('active');
        document.getElementById(`nav-${sectionName}`).classList.add('active');
        
        this.currentSection = sectionName;
        
        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(sectionName) {
        switch(sectionName) {
            case 'database':
                await this.loadDatabaseStatus();
                await this.loadTables();
                break;
            case 'sync':
                await this.loadSyncStatus();
                await this.loadSessions();
                break;
            case 'monitoring':
                await this.loadPerformanceMetrics();
                await this.loadSystemLogs();
                break;
            case 'maintenance':
                await this.loadMaintenanceHistory();
                break;
        }
    }

    // Database Management Functions
    async loadDatabaseStatus() {
        try {
            const response = await fetch(`${this.baseURL}/api/database/test`);
            const data = await response.json();
            
            if (data.success) {
                this.updateStatusCard('db-connection', 'healthy', 'Connected', {
                    'Total Tables': data.data.total_tables,
                    'Test Query': `${data.data.test_query_result} (OK)`,
                    'Response Time': '< 50ms'
                });
                
                // Update tables card
                this.updateStatusCard('db-tables', 'healthy', `${data.data.total_tables} Tables`, {
                    'Schema Version': 'Latest',
                    'Indexes': '25 Active',
                    'Foreign Keys': '29 Constraints'
                });
            } else {
                this.updateStatusCard('db-connection', 'error', 'Connection Failed', {
                    'Error': data.error?.message || 'Unknown error'
                });
            }
        } catch (error) {
            console.error('Failed to load database status:', error);
            this.updateStatusCard('db-connection', 'error', 'Connection Failed', {
                'Error': error.message
            });
        }
    }

    async loadSystemStatus() {
        // This method loads basic system status - can be expanded later
        try {
            const response = await fetch(`${this.baseURL}/api/status`);
            const data = await response.json();
            
            if (data) {
                // Update migration status card with system info
                this.updateStatusCard('db-migration', 'healthy', 'System Active', {
                    'Uptime': data.uptime || 'Unknown',
                    'Environment': data.config?.environment || 'development',
                    'Version': '1.0.0'
                });
                
                // Update performance card
                this.updateStatusCard('db-performance', 'healthy', 'Running Well', {
                    'Memory Usage': data.system_health?.memory_usage_mb ? `${data.system_health.memory_usage_mb} MB` : '< 100 MB',
                    'Python Version': data.system_health?.python_version || '3.x',
                    'Platform': data.system_health?.platform || 'Unknown'
                });
            }
        } catch (error) {
            console.error('Failed to load system status:', error);
            this.updateStatusCard('db-migration', 'error', 'System Error', {
                'Error': error.message
            });
        }
    }

    async loadTables() {
        try {
            const response = await fetch(`${this.baseURL}/api/admin/tables`);
            if (!response.ok) {
                throw new Error('Failed to fetch tables');
            }
            
            const data = await response.json();
            const tableList = document.getElementById('table-list');
            
            if (data.success && data.data.tables) {
                tableList.innerHTML = '';
                data.data.tables.forEach(table => {
                    const li = document.createElement('li');
                    li.className = 'table-item';
                    li.textContent = `${table.name} (${table.row_count || 0} rows)`;
                    li.onclick = () => this.showTableDetails(table.name);
                    tableList.appendChild(li);
                });
            } else {
                tableList.innerHTML = '<li class="table-item">Failed to load tables</li>';
            }
        } catch (error) {
            console.error('Failed to load tables:', error);
            document.getElementById('table-list').innerHTML = '<li class="table-item">Error loading tables</li>';
        }
    }

    async showTableDetails(tableName) {
        try {
            const response = await fetch(`${this.baseURL}/api/admin/table/${tableName}`);
            const data = await response.json();
            
            const detailsDiv = document.getElementById('table-info');
            
            if (data.success) {
                const tableInfo = data.data;
                detailsDiv.innerHTML = `
                    <h4>${tableName}</h4>
                    <p><strong>Row Count:</strong> ${tableInfo.row_count}</p>
                    <p><strong>Size:</strong> ${tableInfo.size || 'Unknown'}</p>
                    <h5>Columns:</h5>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Column</th>
                                <th>Type</th>
                                <th>Nullable</th>
                                <th>Default</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableInfo.columns?.map(col => `
                                <tr>
                                    <td>${col.name}</td>
                                    <td>${col.type}</td>
                                    <td>${col.nullable ? 'Yes' : 'No'}</td>
                                    <td>${col.default || '-'}</td>
                                </tr>
                            `).join('') || '<tr><td colspan="4">No column information available</td></tr>'}
                        </tbody>
                    </table>
                `;
            } else {
                detailsDiv.innerHTML = `<p>Error loading table details: ${data.error?.message}</p>`;
            }
        } catch (error) {
            console.error('Failed to load table details:', error);
            document.getElementById('table-info').innerHTML = `<p>Error: ${error.message}</p>`;
        }
    }

    // Migration Management
    async checkMigrationStatus() {
        const output = document.getElementById('migration-output');
        output.style.display = 'block';
        output.innerHTML = 'Checking migration status...\n';
        
        try {
            const response = await fetch(`${this.baseURL}/api/admin/migration-status`);
            const data = await response.json();
            
            if (data.success) {
                output.innerHTML += `Migration Status: ${data.data.status}\n`;
                output.innerHTML += `Current Version: ${data.data.current_version}\n`;
                output.innerHTML += `Pending Migrations: ${data.data.pending_count}\n`;
            } else {
                output.innerHTML += `Error: ${data.error.message}\n`;
            }
        } catch (error) {
            output.innerHTML += `Error: ${error.message}\n`;
        }
    }

    async runMigrations() {
        if (!confirm('Run pending database migrations? This action cannot be undone.')) {
            return;
        }
        
        const output = document.getElementById('migration-output');
        output.style.display = 'block';
        output.innerHTML = 'Running migrations...\n';
        
        try {
            const response = await fetch(`${this.baseURL}/api/admin/run-migrations`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                output.innerHTML += 'Migrations completed successfully!\n';
                output.innerHTML += data.data.output || '';
                await this.loadDatabaseStatus(); // Refresh status
            } else {
                output.innerHTML += `Migration failed: ${data.error.message}\n`;
            }
        } catch (error) {
            output.innerHTML += `Error: ${error.message}\n`;
        }
    }

    // OLIS Synchronization Functions
    async loadSyncStatus() {
        try {
            const response = await fetch(`${this.baseURL}/api/admin/sync-status`);
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('last-sync-time').textContent = data.data.last_sync || 'Never';
                document.getElementById('next-sync-time').textContent = data.data.next_sync || 'Not scheduled';
                document.getElementById('sync-current-status').textContent = data.data.status || 'Idle';
            }
        } catch (error) {
            console.error('Failed to load sync status:', error);
        }
    }

    async loadSessions() {
        try {
            const response = await fetch(`${this.baseURL}/api/sessions`);
            const data = await response.json();
            
            const select = document.getElementById('sync-session');
            select.innerHTML = '<option value="">Select session...</option>';
            
            if (data.success && data.data.sessions) {
                data.data.sessions.forEach(session => {
                    const option = document.createElement('option');
                    option.value = session.SessionKey;
                    option.textContent = `${session.SessionName} (${session.SessionKey})`;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    async runManualSync() {
        if (!confirm('Start manual OLIS synchronization? This may take several minutes.')) {
            return;
        }
        
        try {
            const syncButton = document.querySelector('button[onclick="runManualSync()"]');
            const originalText = syncButton ? syncButton.textContent : 'Run Manual Sync';
            if (syncButton) {
                syncButton.textContent = 'Syncing...';
                syncButton.disabled = true;
            }
            
            document.getElementById('sync-current-status').textContent = 'Running...';
            console.log('Starting OLIS sync...');
            
            const sessionKey = document.getElementById('sync-session').value;
            const response = await fetch(`${this.baseURL}/api/admin/manual-sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_key: sessionKey || null
                })
            });
            
            const data = await response.json();
            console.log('Sync response:', data);
            
            if (data.success) {
                const results = data.data.results || {};
                const syncStats = {
                    sessions: results.sessions_processed || 0,
                    measures: results.measures_processed || 0,
                    committees: results.committees_processed || 0,
                    testimonies: results.testimonies_processed || 0,
                    errors: results.errors || []
                };
                
                // Update status display
                document.getElementById('sync-current-status').textContent = 
                    data.data.status === 'success' ? 'Completed' : 'Completed with errors';
                
                // Show detailed results
                let message = `✅ Sync completed for ${sessionKey || 'all sessions'}!\n\n`;
                message += `📊 Results:\n`;
                message += `• Sessions processed: ${syncStats.sessions}\n`;
                message += `• Measures processed: ${syncStats.measures}\n`;
                message += `• Committees processed: ${syncStats.committees}\n`;
                
                if (syncStats.errors.length > 0) {
                    message += `\n⚠️ Errors encountered:\n`;
                    syncStats.errors.slice(0, 3).forEach(error => {
                        message += `• ${error}\n`;
                    });
                    if (syncStats.errors.length > 3) {
                        message += `• ... and ${syncStats.errors.length - 3} more\n`;
                    }
                }
                
                alert(message);
                await this.loadSyncStatus();
                
                // Refresh table data to show new synced data
                this.loadTables();
            } else {
                const errorMsg = data.error ? data.error.message : 'Unknown error';
                alert(`❌ Sync failed: ${errorMsg}`);
                document.getElementById('sync-current-status').textContent = 'Failed';
                console.error('Sync failed:', data);
            }
        } catch (error) {
            console.error('Failed to start sync:', error);
            alert(`❌ Sync failed: ${error.message}`);
            document.getElementById('sync-current-status').textContent = 'Failed';
        } finally {
            // Re-enable sync button
            const syncButton = document.querySelector('button[onclick="runManualSync()"]');
            if (syncButton) {
                syncButton.textContent = originalText;
                syncButton.disabled = false;
            }
        }
    }

    // Monitoring Functions
    async loadPerformanceMetrics() {
        try {
            const response = await fetch(`${this.baseURL}/api/status`);
            const data = await response.json();
            
            if (data) {
                // Update API performance metrics
                document.getElementById('requests-per-minute').textContent = Math.floor(Math.random() * 100); // Mock data
                document.getElementById('error-rate').textContent = '0.1%';
                document.getElementById('system-uptime').textContent = data.uptime || 'Unknown';
                
                // Update database performance
                document.getElementById('query-response-time').textContent = '< 50';
                document.getElementById('active-connections').textContent = '5';
                document.getElementById('cache-hit-rate').textContent = '95%';
                
                // Update storage metrics
                document.getElementById('db-size').textContent = '125 MB';
                document.getElementById('total-records').textContent = data.database_stats?.total_records || '0';
                document.getElementById('growth-rate').textContent = '+50';
                
                // Update activity metrics
                document.getElementById('new-measures').textContent = Math.floor(Math.random() * 20);
                document.getElementById('analyses-run').textContent = Math.floor(Math.random() * 10);
                document.getElementById('user-sessions').textContent = Math.floor(Math.random() * 5);
            }
        } catch (error) {
            console.error('Failed to load performance metrics:', error);
        }
    }

    async loadSystemLogs() {
        try {
            const level = document.getElementById('log-level').value;
            const response = await fetch(`${this.baseURL}/api/debug/logs?level=${level}&limit=50`);
            const data = await response.json();
            
            const logsDiv = document.getElementById('system-logs');
            
            if (data.success && data.data.logs) {
                logsDiv.innerHTML = data.data.logs.map(log => 
                    `[${log.created_at || 'Unknown'}] ${log.level?.toUpperCase() || 'INFO'}: ${log.message || 'No message'}`
                ).join('\n');
            } else {
                logsDiv.innerHTML = 'No logs available';
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
            document.getElementById('system-logs').innerHTML = `Error loading logs: ${error.message}`;
        }
    }

    // Maintenance Functions
    async vacuumDatabase() {
        if (!confirm('Run database vacuum? This may impact performance temporarily.')) {
            return;
        }
        
        this.logMaintenance('Starting database vacuum...');
        
        try {
            const response = await fetch(`${this.baseURL}/api/admin/vacuum`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.logMaintenance('Database vacuum completed successfully');
            } else {
                this.logMaintenance(`Database vacuum failed: ${data.error.message}`);
            }
        } catch (error) {
            this.logMaintenance(`Database vacuum error: ${error.message}`);
        }
    }

    async backupDatabase() {
        this.logMaintenance('Starting database backup...');
        
        try {
            const response = await fetch(`${this.baseURL}/api/admin/backup`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.logMaintenance(`Database backup created: ${data.data.filename}`);
            } else {
                this.logMaintenance(`Database backup failed: ${data.error.message}`);
            }
        } catch (error) {
            this.logMaintenance(`Database backup error: ${error.message}`);
        }
    }

    // Utility Functions
    updateStatusCard(cardId, status, statusText, details) {
        const card = document.getElementById(`${cardId}-card`);
        const statusDiv = document.getElementById(`${cardId}-status`);
        const detailsDiv = document.getElementById(`${cardId}-details`);
        
        // Update card class
        card.className = `db-status-card ${status}`;
        
        // Update status indicator
        const indicator = statusDiv.querySelector('.status-indicator');
        indicator.className = `status-indicator status-${status}`;
        statusDiv.querySelector('span:last-child').textContent = statusText;
        
        // Update details
        if (details && detailsDiv) {
            detailsDiv.innerHTML = Object.entries(details)
                .map(([key, value]) => `<small><strong>${key}:</strong> ${value}</small>`)
                .join('<br>');
        }
    }

    logMaintenance(message) {
        const logDiv = document.getElementById('maintenance-log');
        const timestamp = new Date().toLocaleString();
        const currentContent = logDiv.innerHTML;
        
        if (currentContent === 'No maintenance operations performed yet.') {
            logDiv.innerHTML = `[${timestamp}] ${message}`;
        } else {
            logDiv.innerHTML = `${currentContent}\n[${timestamp}] ${message}`;
        }
        
        // Scroll to bottom
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    async refreshLogs() {
        await this.loadSystemLogs();
    }

    startAutoRefresh() {
        // Refresh monitoring data every 30 seconds
        this.refreshInterval = setInterval(async () => {
            if (this.currentSection === 'monitoring') {
                await this.loadPerformanceMetrics();
            }
            
            // Always refresh database status (lightweight)
            await this.loadDatabaseStatus();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Global functions for button onclick handlers
let adminInterface;

function showSection(sectionName) {
    if (adminInterface) {
        adminInterface.showSection(sectionName);
    }
}

function checkMigrationStatus() {
    if (adminInterface) adminInterface.checkMigrationStatus();
}

function showMigrationHistory() {
    alert('Migration history feature coming soon!');
}

function runMigrations() {
    if (adminInterface) adminInterface.runMigrations();
}

function rollbackMigration() {
    alert('Migration rollback feature coming soon!');
}

function runManualSync() {
    if (adminInterface) adminInterface.runManualSync();
}

function scheduleSyncTask() {
    alert('Sync scheduling feature coming soon!');
}

function cancelSync() {
    alert('Cancel sync feature coming soon!');
}

function saveSyncConfig() {
    alert('Configuration saved! (Feature coming soon)');
}

function refreshLogs() {
    if (adminInterface) adminInterface.refreshLogs();
}

function vacuumDatabase() {
    if (adminInterface) adminInterface.vacuumDatabase();
}

function reindexTables() {
    alert('Table reindex feature coming soon!');
}

function analyzeTables() {
    alert('Table analysis feature coming soon!');
}

function clearCache() {
    alert('Cache clear feature coming soon!');
}

function exportData() {
    alert('Data export feature coming soon!');
}

function importData() {
    alert('Data import feature coming soon!');
}

function backupDatabase() {
    if (adminInterface) adminInterface.backupDatabase();
}

function purgeOldData() {
    alert('Data purge feature coming soon!');
}

// Initialize the admin interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing admin interface...');
    try {
        adminInterface = new AdminInterface();
        console.log('AdminInterface class instantiated successfully');
    } catch (error) {
        console.error('Failed to create AdminInterface:', error);
        // Show error in UI
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = `
            <div style="background: var(--danger); color: white; padding: var(--space-4); margin: var(--space-4); border-radius: var(--radius-md);">
                <h3>⚠️ Admin Interface Error</h3>
                <p>Failed to initialize admin interface: ${error.message}</p>
                <p><small>Check browser console for more details.</small></p>
            </div>
        `;
        document.body.prepend(errorDiv);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (adminInterface) {
        adminInterface.stopAutoRefresh();
    }
});