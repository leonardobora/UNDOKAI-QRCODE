// Dashboard JavaScript for Lightera BUNDOKAI
class Dashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.isVisible = true;
        this.lastUpdateTime = new Date();
        this.newCheckinIds = new Set();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupVisibilityChange();
        this.startAutoRefresh();
        this.setupKeyboardShortcuts();
        this.setupMobileSearch();
        this.setupAccessibility();
    }

    setupEventListeners() {
        // Manual refresh button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[onclick*="refreshDashboard"]') || 
                e.target.closest('[onclick*="refreshDashboard"]')) {
                this.refreshDashboard();
            }
        });

        // Connection status check
        window.addEventListener('online', () => this.updateConnectionStatus(true));
        window.addEventListener('offline', () => this.updateConnectionStatus(false));
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + S for Scanner
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                this.openScanner();
            }
            
            // Alt + B for Search
            if (e.altKey && e.key === 'b') {
                e.preventDefault();
                this.openSearch();
            }
            
            // Alt + D for Dashboard
            if (e.altKey && e.key === 'd') {
                e.preventDefault();
                location.reload();
            }
            
            // Alt + A for Admin
            if (e.altKey && e.key === 'a') {
                e.preventDefault();
                window.open('/admin/panel', '_blank');
            }
            
            // Alt + E for Export
            if (e.altKey && e.key === 'e') {
                e.preventDefault();
                this.exportData();
            }
            
            // Alt + R for Report
            if (e.altKey && e.key === 'r') {
                e.preventDefault();
                this.sendReport();
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal.show');
                modals.forEach(modal => {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) modalInstance.hide();
                });
            }
        });
    }

    setupMobileSearch() {
        const mobileSearch = document.getElementById('mobile-search');
        if (mobileSearch) {
            let searchTimeout;
            mobileSearch.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    // Redirect to search page with query
                    if (e.target.value.trim()) {
                        window.location.href = `/checkin/search?q=${encodeURIComponent(e.target.value)}`;
                    }
                }, 500);
            });
        }
    }

    setupAccessibility() {
        // Add focus management for card navigation
        const statsCards = document.querySelectorAll('.stats-card-enhanced');
        statsCards.forEach(card => {
            card.addEventListener('focus', () => {
                card.style.outline = '3px solid var(--lightera-purple)';
                card.style.outlineOffset = '2px';
            });
            
            card.addEventListener('blur', () => {
                card.style.outline = 'none';
            });
        });

        // Announce updates to screen readers
        this.setupLiveRegions();
    }

    setupLiveRegions() {
        const liveRegions = document.querySelectorAll('[aria-live]');
        liveRegions.forEach(region => {
            region.setAttribute('aria-atomic', 'true');
        });
    }

    setupVisibilityChange() {
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            if (this.isVisible) {
                this.refreshDashboard();
            }
        });
    }

    startAutoRefresh() {
        // Refresh every 30 seconds when page is visible
        this.refreshInterval = setInterval(() => {
            if (this.isVisible) {
                this.refreshDashboard();
            }
        }, 30000);
    }

    initializeDashboard(hourlyData, statsData) {
        this.createHourlyChart(hourlyData);
        this.createStatusChart(statsData);
        this.updateStats(statsData);
        this.updateLastUpdateTime();
    }

    createHourlyChart(hourlyData) {
        const ctx = document.getElementById('hourlyChart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.hourly) {
            this.charts.hourly.destroy();
        }

        const hours = hourlyData.map(d => `${d.hour}:00`);
        const counts = hourlyData.map(d => d.count);

        this.charts.hourly = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: hours,
                datasets: [{
                    label: 'Check-ins',
                    data: counts,
                    backgroundColor: 'rgba(111, 66, 193, 0.7)',
                    borderColor: 'rgba(111, 66, 193, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(111, 66, 193, 1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                return `Horário: ${context[0].label}`;
                            },
                            label: function(context) {
                                return `Check-ins: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            color: '#6c757d'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#6c757d'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    createStatusChart(statsData) {
        const ctx = document.getElementById('statusChart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.status) {
            this.charts.status.destroy();
        }

        const checkedIn = statsData.total_checkins;
        const pending = statsData.pending_checkins;

        this.charts.status = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Check-in realizado', 'Aguardando'],
                datasets: [{
                    data: [checkedIn, pending],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(255, 193, 7, 0.8)'
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(255, 193, 7, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            color: '#495057'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(111, 66, 193, 1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    updateStats(statsData) {
        // Update counter elements with animation
        this.animateCounter('total-participants', statsData.total_participants);
        this.animateCounter('total-checkins', statsData.total_checkins);
        this.animateCounter('pending-checkins', statsData.pending_checkins);
        
        // Calculate and update attendance rate
        const attendanceRate = statsData.total_participants > 0 
            ? (statsData.total_checkins / statsData.total_participants * 100).toFixed(1)
            : 0;
        this.animateCounter('attendance-rate', attendanceRate, '%');
        
        // Update percentage in success card
        const percentageEl = document.getElementById('attendance-percentage');
        if (percentageEl) {
            percentageEl.textContent = `${attendanceRate}%`;
        }
        
        // Update pending indicator based on count
        const pendingCard = document.querySelector('.pending-indicator');
        if (pendingCard) {
            if (statsData.pending_checkins > 0) {
                pendingCard.classList.add('pending-indicator');
            } else {
                pendingCard.classList.remove('pending-indicator');
            }
        }
        
        // Announce significant changes to screen readers
        this.announceChanges(statsData);
    }

    animateCounter(elementId, targetValue, suffix = '') {
        const element = document.getElementById(elementId);
        if (!element) return;

        const currentValue = parseInt(element.textContent) || 0;
        const increment = (targetValue - currentValue) / 20;
        let current = currentValue;
        
        // Add highlight class for visual feedback
        element.parentElement?.classList.add('success-animation');
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= targetValue) || 
                (increment < 0 && current <= targetValue)) {
                current = targetValue;
                clearInterval(timer);
                element.parentElement?.classList.remove('success-animation');
            }
            element.textContent = Math.floor(current) + suffix;
        }, 50);
    }

    announceChanges(statsData) {
        // Announce significant changes for accessibility
        const announcements = [];
        
        if (statsData.total_checkins > this.lastStats?.total_checkins) {
            const newCheckins = statsData.total_checkins - (this.lastStats?.total_checkins || 0);
            announcements.push(`${newCheckins} novo${newCheckins > 1 ? 's' : ''} check-in${newCheckins > 1 ? 's' : ''} realizado${newCheckins > 1 ? 's' : ''}`);
        }
        
        if (announcements.length > 0) {
            this.announceToScreenReader(announcements.join('. '));
        }
        
        this.lastStats = {...statsData};
    }

    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    updateRecentCheckins(recentCheckins) {
        const tbody = document.getElementById('recent-checkins-tbody');
        if (!tbody || !recentCheckins) return;

        if (recentCheckins.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        <i class="fas fa-info-circle" aria-hidden="true"></i>
                        Nenhum check-in realizado ainda
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = recentCheckins.map((checkin, index) => {
            const isNew = this.newCheckinIds.has(checkin.checkin_time + checkin.nome);
            const rowClass = isNew ? 'new-checkin-row' : '';
            
            return `
                <tr class="fade-in ${rowClass}" role="row">
                    <td>${checkin.checkin_time}</td>
                    <td>
                        <div class="fw-bold">${checkin.nome}</div>
                        <small class="text-muted">${checkin.email || ''}</small>
                    </td>
                    <td>${checkin.departamento || '-'}</td>
                    <td class="text-center">
                        ${checkin.dependents_count > 0 ? 
                            `<span class="enhanced-badge bg-info" aria-label="${checkin.dependents_count} dependentes">${checkin.dependents_count}</span>` : 
                            '<span aria-label="Nenhum dependente">-</span>'
                        }
                    </td>
                    <td>
                        <span class="enhanced-badge bg-secondary" aria-label="Estação ${checkin.station}">
                            ${checkin.station}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Mark new check-ins
        if (this.lastCheckins) {
            recentCheckins.forEach(checkin => {
                const key = checkin.checkin_time + checkin.nome;
                const isNew = !this.lastCheckins.some(old => 
                    old.checkin_time + old.nome === key
                );
                if (isNew) {
                    this.newCheckinIds.add(key);
                    setTimeout(() => this.newCheckinIds.delete(key), 5000);
                }
            });
        }
        
        this.lastCheckins = [...recentCheckins];
    }

    refreshDashboard() {
        fetch('/api/dashboard_stats')
            .then(response => response.json())
            .then(data => {
                this.updateStats(data);
                this.updateRecentCheckins(data.recent_checkins);
                this.updateLastUpdateTime();
                this.updateConnectionStatus(true);
            })
            .catch(error => {
                console.error('Failed to refresh dashboard:', error);
                this.updateConnectionStatus(false);
                this.showErrorToast('Erro ao atualizar dashboard');
            });
    }

    refreshRecentCheckins() {
        fetch('/api/recent_checkins')
            .then(response => response.json())
            .then(data => {
                this.updateRecentCheckins(data.recent_checkins);
                this.updateLastUpdateTime();
                this.showSuccessToast('Check-ins atualizados');
            })
            .catch(error => {
                console.error('Failed to refresh recent check-ins:', error);
                this.showErrorToast('Erro ao atualizar check-ins');
            });
    }

    updateLastUpdateTime() {
        this.lastUpdateTime = new Date();
        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) {
            lastUpdateEl.textContent = this.lastUpdateTime.toLocaleTimeString();
        }
    }

    updateConnectionStatus(isOnline) {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            if (isOnline) {
                statusEl.innerHTML = '<i class="fas fa-wifi" aria-hidden="true"></i> Online';
                statusEl.className = 'enhanced-badge status-checked-in';
            } else {
                statusEl.innerHTML = '<i class="fas fa-wifi-slash" aria-hidden="true"></i> Offline';
                statusEl.className = 'enhanced-badge status-pending';
            }
        }
    }

    showSuccessToast(message) {
        this.showToast(message, 'success');
    }

    showErrorToast(message) {
        this.showToast(message, 'danger');
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toastContainer.removeChild(toast);
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    // Helper methods for global functions
    openScanner() {
        window.open('/scanner', '_blank');
    }

    openSearch() {
        window.open('/checkin/search', '_blank');
    }

    exportData() {
        window.location.href = '/api/export/checkins';
    }

    sendReport() {
        if (confirm('Enviar relatório atual por email?')) {
            fetch('/api/send_report', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.showSuccessToast('Relatório enviado com sucesso!');
                    } else {
                        this.showErrorToast('Erro ao enviar relatório');
                    }
                })
                .catch(error => {
                    console.error('Send report error:', error);
                    this.showErrorToast('Erro ao enviar relatório');
                });
        }
    }

    destroy() {
        // Cleanup when component is destroyed
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
    }
}

// Global functions for template
function refreshDashboard() {
    if (window.dashboardInstance) {
        window.dashboardInstance.refreshDashboard();
    }
}

function refreshRecentCheckins() {
    if (window.dashboardInstance) {
        window.dashboardInstance.refreshRecentCheckins();
    }
}

function initializeDashboard(hourlyData, statsData) {
    if (window.dashboardInstance) {
        window.dashboardInstance.initializeDashboard(hourlyData, statsData);
    }
}

function exportData() {
    if (window.dashboardInstance) {
        window.dashboardInstance.exportData();
    }
}

function sendReport() {
    if (window.dashboardInstance) {
        window.dashboardInstance.sendReport();
    }
}

function openScanner() {
    if (window.dashboardInstance) {
        window.dashboardInstance.openScanner();
    }
}

function openSearch() {
    if (window.dashboardInstance) {
        window.dashboardInstance.openSearch();
    }
}

// Accessibility helpers
function handleCardKeypress(event, action) {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        switch(action) {
            case 'scanner':
                openScanner();
                break;
            case 'search':
                openSearch();
                break;
            case 'export':
                exportData();
                break;
            case 'report':
                sendReport();
                break;
            default:
                // Focus on related section
                focusSection(action);
        }
    }
}

function focusSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.focus();
        section.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Connection status checker
function checkConnectionStatus() {
    if (window.dashboardInstance) {
        window.dashboardInstance.updateConnectionStatus(navigator.onLine);
    }
}
        const ctx = document.getElementById('hourlyChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.hourly) {
            this.charts.hourly.destroy();
        }

        const hours = hourlyData.map(item => `${item.hour}:00`);
        const counts = hourlyData.map(item => item.count);

        this.charts.hourly = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [{
                    label: 'Check-ins por Hora',
                    data: counts,
                    borderColor: '#6f42c1',
                    backgroundColor: 'rgba(111, 66, 193, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#6f42c1',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#6f42c1',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `Check-ins: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: '#666'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: '#666',
                            stepSize: 1
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    createStatusChart(statsData) {
        const ctx = document.getElementById('statusChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.status) {
            this.charts.status.destroy();
        }

        const data = [
            statsData.total_checkins,
            statsData.pending_checkins
        ];

        const colors = ['#28a745', '#ffc107'];

        this.charts.status = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Check-ins Realizados', 'Aguardando Check-in'],
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#ffffff',
                    borderWidth: 3,
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            color: '#666'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#6f42c1',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    updateStats(statsData) {
        // Update counter elements with animation
        this.animateCounter('total-participants', statsData.total_participants);
        this.animateCounter('total-checkins', statsData.total_checkins);
        this.animateCounter('pending-checkins', statsData.pending_checkins);
        
        // Calculate and update attendance rate
        const attendanceRate = statsData.total_participants > 0 
            ? (statsData.total_checkins / statsData.total_participants * 100).toFixed(1)
            : 0;
        this.animateCounter('attendance-rate', attendanceRate, '%');
    }

    animateCounter(elementId, targetValue, suffix = '') {
        const element = document.getElementById(elementId);
        if (!element) return;

        const currentValue = parseInt(element.textContent) || 0;
        const increment = targetValue > currentValue ? 1 : -1;
        const stepTime = Math.abs(Math.floor(300 / (targetValue - currentValue)));

        if (targetValue === currentValue) return;

        const timer = setInterval(() => {
            const current = parseInt(element.textContent) || 0;
            
            if ((increment > 0 && current >= targetValue) || 
                (increment < 0 && current <= targetValue)) {
                element.textContent = targetValue + suffix;
                clearInterval(timer);
            } else {
                element.textContent = (current + increment) + suffix;
            }
        }, stepTime);
    }

    refreshDashboard() {
        this.showRefreshIndicator();
        
        fetch('/api/dashboard_stats')
            .then(response => response.json())
            .then(data => {
                this.updateStats(data);
                this.updateRecentCheckins(data.recent_checkins);
                this.updateStatusChart(data);
                this.showRefreshSuccess();
                this.updateLastRefreshTime();
            })
            .catch(error => {
                console.error('Failed to refresh dashboard:', error);
                this.showRefreshError();
            });
    }

    updateRecentCheckins(recentCheckins) {
        const tbody = document.getElementById('recent-checkins-tbody');
        if (!tbody || !recentCheckins) return;

        if (recentCheckins.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        Nenhum check-in realizado ainda
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = recentCheckins.map(checkin => `
            <tr class="fade-in">
                <td>${checkin.checkin_time}</td>
                <td>${checkin.nome}</td>
                <td>${checkin.departamento || '-'}</td>
                <td class="text-center">
                    ${checkin.dependents_count > 0 ? 
                        `<span class="badge bg-info">${checkin.dependents_count}</span>` : 
                        '-'
                    }
                </td>
                <td>
                    <span class="badge bg-secondary">${checkin.station}</span>
                </td>
            </tr>
        `).join('');
    }

    updateStatusChart(data) {
        if (this.charts.status) {
            this.charts.status.data.datasets[0].data = [
                data.total_checkins,
                data.pending_checkins
            ];
            this.charts.status.update('active');
        }
    }

    showRefreshIndicator() {
        const refreshButtons = document.querySelectorAll('[onclick*="refreshDashboard"]');
        refreshButtons.forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-spinner fa-spin';
            }
            btn.disabled = true;
        });
    }

    showRefreshSuccess() {
        const refreshButtons = document.querySelectorAll('[onclick*="refreshDashboard"]');
        refreshButtons.forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-sync';
            }
            btn.disabled = false;
        });

        // Show toast notification
        this.showToast('Dados atualizados com sucesso!', 'success');
    }

    showRefreshError() {
        const refreshButtons = document.querySelectorAll('[onclick*="refreshDashboard"]');
        refreshButtons.forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-exclamation-triangle';
            }
            btn.disabled = false;
        });

        this.showToast('Erro ao atualizar dados', 'error');
    }

    updateLastRefreshTime() {
        const lastUpdateElement = document.getElementById('last-update');
        if (lastUpdateElement) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('pt-BR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            lastUpdateElement.textContent = timeString;
        }
    }

    showToast(message, type = 'info') {
        const toastElement = document.getElementById('refresh-toast');
        if (!toastElement) return;

        const toastBody = toastElement.querySelector('.toast-body');
        const toastHeader = toastElement.querySelector('.toast-header i');
        
        toastBody.textContent = message;
        
        // Update icon based on type
        if (type === 'success') {
            toastHeader.className = 'fas fa-check-circle text-success me-2';
        } else if (type === 'error') {
            toastHeader.className = 'fas fa-exclamation-circle text-danger me-2';
        } else {
            toastHeader.className = 'fas fa-info-circle text-primary me-2';
        }
        
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }

    refreshRecentCheckins() {
        fetch('/api/recent_checkins')
            .then(response => response.json())
            .then(data => {
                this.updateRecentCheckins(data.recent_checkins);
            })
            .catch(error => {
                console.error('Failed to refresh recent check-ins:', error);
            });
    }

    destroy() {
        // Cleanup when component is destroyed
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
    }
}

// Global functions for template
function refreshDashboard() {
    if (window.dashboardInstance) {
        window.dashboardInstance.refreshDashboard();
    }
}

function refreshRecentCheckins() {
    if (window.dashboardInstance) {
        window.dashboardInstance.refreshRecentCheckins();
    }
}

function initializeDashboard(hourlyData, statsData) {
    if (window.dashboardInstance) {
        window.dashboardInstance.initializeDashboard(hourlyData, statsData);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardInstance = new Dashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.dashboardInstance) {
        window.dashboardInstance.destroy();
    }
});

// Real-time updates using WebSocket (if available)
function initializeWebSocket() {
    if (typeof WebSocket !== 'undefined') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
        
        try {
            const ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('WebSocket connected for real-time updates');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'checkin_update' && window.dashboardInstance) {
                    window.dashboardInstance.refreshDashboard();
                }
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected - falling back to polling');
            };
            
            ws.onerror = function(error) {
                console.warn('WebSocket error:', error);
            };
            
        } catch (error) {
            console.warn('WebSocket not available, using polling only');
        }
    }
}

// Try to initialize WebSocket for real-time updates
setTimeout(initializeWebSocket, 1000);
