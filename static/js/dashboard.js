// Dashboard JavaScript for Lightera BUNDOKAI
class Dashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.isVisible = true;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupVisibilityChange();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Manual refresh button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[onclick*="refreshDashboard"]') || 
                e.target.closest('[onclick*="refreshDashboard"]')) {
                this.refreshDashboard();
            }
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
    }

    createHourlyChart(hourlyData) {
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
