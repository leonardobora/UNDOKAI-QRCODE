// QR Code Scanner JavaScript for Lightera BUNDOKAI
class QRScanner {
    constructor() {
        this.html5QrcodeScanner = null;
        this.isScanning = false;
        this.stats = {
            scansToday: 0,
            successfulCheckins: 0,
            failedScans: 0,
            duplicateAttempts: 0
        };
        this.recentScans = [];
        this.init();
    }

    init() {
        this.loadStats();
        this.setupEventListeners();
        this.updateStatsDisplay();
    }

    setupEventListeners() {
        document.getElementById('start-scan').addEventListener('click', () => this.startScanning());
        document.getElementById('stop-scan').addEventListener('click', () => this.stopScanning());
        document.getElementById('switch-camera').addEventListener('click', () => this.switchCamera());
        
        // Manual QR input
        document.getElementById('manual-qr').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.validateManualQR();
            }
        });

        // Auto-refresh dashboard stats every 30 seconds
        setInterval(() => this.refreshDashboardStats(), 30000);
    }

    startScanning() {
        if (this.isScanning) return;

        const config = {
            fps: 10,
            qrbox: { width: 250, height: 250 },
            aspectRatio: 1.0,
            disableFlip: false,
            supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA]
        };

        this.html5QrcodeScanner = new Html5Qrcode("qr-reader");
        
        this.html5QrcodeScanner.start(
            { facingMode: "environment" }, // Use back camera
            config,
            (decodedText, decodedResult) => this.onScanSuccess(decodedText, decodedResult),
            (errorMessage) => this.onScanError(errorMessage)
        ).then(() => {
            this.isScanning = true;
            this.updateScannerUI(true);
        }).catch(err => {
            console.error('Failed to start scanner:', err);
            this.showError('Erro ao iniciar câmera. Verifique as permissões.');
        });
    }

    stopScanning() {
        if (!this.isScanning || !this.html5QrcodeScanner) return;

        this.html5QrcodeScanner.stop().then(() => {
            this.isScanning = false;
            this.updateScannerUI(false);
        }).catch(err => {
            console.error('Failed to stop scanner:', err);
        });
    }

    switchCamera() {
        if (!this.isScanning) return;
        
        this.stopScanning();
        setTimeout(() => {
            // Try to start with front camera
            const config = {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0
            };

            this.html5QrcodeScanner.start(
                { facingMode: "user" }, // Use front camera
                config,
                (decodedText, decodedResult) => this.onScanSuccess(decodedText, decodedResult),
                (errorMessage) => this.onScanError(errorMessage)
            ).then(() => {
                this.isScanning = true;
                this.updateScannerUI(true);
            }).catch(err => {
                console.error('Failed to switch camera:', err);
                // Fallback to environment camera
                this.startScanning();
            });
        }, 500);
    }

    onScanSuccess(decodedText, decodedResult) {
        console.log('QR Code detected:', decodedText);
        
        // Temporarily stop scanning to prevent multiple scans
        this.html5QrcodeScanner.pause(true);
        
        // Clean and validate QR code
        const qrCode = decodedText.trim().toUpperCase();
        this.validateQRCode(qrCode);
        
        // Resume scanning after 2 seconds
        setTimeout(() => {
            if (this.html5QrcodeScanner && this.isScanning) {
                this.html5QrcodeScanner.resume();
            }
        }, 2000);
    }

    onScanError(errorMessage) {
        // Don't log every frame error, just major issues
        if (errorMessage.includes('No QR code found')) {
            return;
        }
        console.warn('QR Scan error:', errorMessage);
    }

    validateQRCode(qrCode) {
        this.stats.scansToday++;
        this.updateStatsDisplay();

        // Show loading state
        this.showValidating();

        const requestData = {
            qr_code: qrCode,
            station: 'scanner',
            operator: 'Sistema Scanner'
        };

        fetch('/api/validate_qr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            this.hideValidating();
            
            if (data.success) {
                this.handleSuccessfulCheckin(data.participant, qrCode);
            } else {
                this.handleFailedCheckin(data.message, qrCode, data.already_checked_in);
            }
        })
        .catch(error => {
            this.hideValidating();
            console.error('Validation error:', error);
            this.handleFailedCheckin('Erro de conexão. Tente novamente.', qrCode);
        });
    }

    validateManualQR() {
        const qrCode = document.getElementById('manual-qr').value.trim().toUpperCase();
        if (qrCode) {
            this.validateQRCode(qrCode);
            document.getElementById('manual-qr').value = '';
        }
    }

    handleSuccessfulCheckin(participant, qrCode) {
        this.stats.successfulCheckins++;
        this.updateStatsDisplay();
        
        // Add to recent scans
        this.addRecentScan({
            time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
            participant: participant.nome,
            code: qrCode,
            status: 'success'
        });

        // Show success modal
        this.showSuccessModal(participant);
        
        // Play success sound (if available)
        this.playSound('success');
    }

    handleFailedCheckin(message, qrCode, isDuplicate = false) {
        if (isDuplicate) {
            this.stats.duplicateAttempts++;
        } else {
            this.stats.failedScans++;
        }
        this.updateStatsDisplay();
        
        // Add to recent scans
        this.addRecentScan({
            time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
            participant: 'N/A',
            code: qrCode,
            status: isDuplicate ? 'duplicate' : 'error'
        });

        // Show error modal
        this.showErrorModal(message);
        
        // Play error sound (if available)
        this.playSound('error');
    }

    showSuccessModal(participant) {
        const modal = document.getElementById('successModal');
        const content = document.getElementById('success-content');
        
        content.innerHTML = `
            <div class="text-center mb-3">
                <i class="fas fa-check-circle fa-4x text-success"></i>
            </div>
            <h5 class="text-center mb-3">Check-in Realizado com Sucesso!</h5>
            <div class="card">
                <div class="card-body">
                    <h6><strong>Participante:</strong></h6>
                    <p class="mb-2">${participant.nome}</p>
                    
                    <h6><strong>Email:</strong></h6>
                    <p class="mb-2">${participant.email}</p>
                    
                    ${participant.departamento ? `
                        <h6><strong>Departamento:</strong></h6>
                        <p class="mb-2">${participant.departamento}</p>
                    ` : ''}
                    
                    <h6><strong>Dependentes:</strong></h6>
                    <p class="mb-2">${participant.dependents_count} pessoa(s)</p>
                    
                    <h6><strong>Horário do Check-in:</strong></h6>
                    <p class="mb-0 text-primary fw-bold">${participant.checkin_time}</p>
                </div>
            </div>
        `;
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            bsModal.hide();
        }, 5000);
    }

    showErrorModal(message) {
        const modal = document.getElementById('errorModal');
        const content = document.getElementById('error-content');
        
        content.innerHTML = `
            <div class="text-center mb-3">
                <i class="fas fa-exclamation-triangle fa-3x text-danger"></i>
            </div>
            <div class="alert alert-danger">
                <strong>Erro no Check-in:</strong><br>
                ${message}
            </div>
            <div class="text-muted">
                <h6>Possíveis soluções:</h6>
                <ul>
                    <li>Verifique se o QR Code está correto</li>
                    <li>Certifique-se de que o participante está inscrito</li>
                    <li>Tente usar a busca manual por nome</li>
                    <li>Entre em contato com o suporte se o problema persistir</li>
                </ul>
            </div>
        `;
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    showValidating() {
        const resultContainer = document.getElementById('scan-result');
        resultContainer.innerHTML = `
            <div class="alert alert-info text-center">
                <div class="spinner-border text-primary me-2" role="status">
                    <span class="visually-hidden">Validando...</span>
                </div>
                Validando QR Code...
            </div>
        `;
        resultContainer.style.display = 'block';
    }

    hideValidating() {
        const resultContainer = document.getElementById('scan-result');
        resultContainer.style.display = 'none';
    }

    updateScannerUI(isScanning) {
        const startBtn = document.getElementById('start-scan');
        const stopBtn = document.getElementById('stop-scan');
        const switchBtn = document.getElementById('switch-camera');
        
        startBtn.style.display = isScanning ? 'none' : 'inline-block';
        stopBtn.style.display = isScanning ? 'inline-block' : 'none';
        switchBtn.style.display = isScanning ? 'inline-block' : 'none';
    }

    updateStatsDisplay() {
        document.getElementById('scans-today').textContent = this.stats.scansToday;
        document.getElementById('successful-checkins').textContent = this.stats.successfulCheckins;
        document.getElementById('failed-scans').textContent = this.stats.failedScans;
        document.getElementById('duplicate-attempts').textContent = this.stats.duplicateAttempts;
        
        // Save stats to localStorage
        localStorage.setItem('scannerStats', JSON.stringify(this.stats));
    }

    loadStats() {
        const saved = localStorage.getItem('scannerStats');
        if (saved) {
            this.stats = { ...this.stats, ...JSON.parse(saved) };
        }
        
        // Reset daily stats if it's a new day
        const lastResetDate = localStorage.getItem('lastStatsReset');
        const today = new Date().toDateString();
        
        if (lastResetDate !== today) {
            this.stats.scansToday = 0;
            this.stats.successfulCheckins = 0;
            this.stats.failedScans = 0;
            this.stats.duplicateAttempts = 0;
            localStorage.setItem('lastStatsReset', today);
        }
    }

    addRecentScan(scan) {
        this.recentScans.unshift(scan);
        if (this.recentScans.length > 10) {
            this.recentScans.pop();
        }
        this.updateRecentScansDisplay();
    }

    updateRecentScansDisplay() {
        const tbody = document.getElementById('recent-scans-tbody');
        
        if (this.recentScans.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum scan realizado ainda</td></tr>';
            return;
        }
        
        tbody.innerHTML = this.recentScans.map(scan => `
            <tr>
                <td>${scan.time}</td>
                <td>${scan.participant}</td>
                <td><code>${scan.code}</code></td>
                <td>
                    ${scan.status === 'success' ? '<span class="badge bg-success">Sucesso</span>' :
                      scan.status === 'duplicate' ? '<span class="badge bg-warning">Duplicado</span>' :
                      '<span class="badge bg-danger">Erro</span>'}
                </td>
            </tr>
        `).join('');
    }

    refreshDashboardStats() {
        fetch('/api/dashboard_stats')
            .then(response => response.json())
            .then(data => {
                // Update any dashboard elements if needed
                console.log('Dashboard stats refreshed:', data);
            })
            .catch(error => {
                console.warn('Failed to refresh dashboard stats:', error);
            });
    }

    playSound(type) {
        // Simple audio feedback using Web Audio API
        if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            if (type === 'success') {
                // High-pitched success sound
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
            } else {
                // Low-pitched error sound
                oscillator.frequency.setValueAtTime(300, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(200, audioContext.currentTime + 0.2);
            }
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        }
    }
}

// Global functions for template
function tryAgain() {
    // Close error modal and focus on manual input
    const modal = bootstrap.Modal.getInstance(document.getElementById('errorModal'));
    if (modal) {
        modal.hide();
    }
    document.getElementById('manual-qr').focus();
}

function validateManualQR() {
    if (window.qrScanner) {
        window.qrScanner.validateManualQR();
    }
}

// Initialize scanner when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.qrScanner = new QRScanner();
});

// Handle page visibility changes (pause/resume scanning)
document.addEventListener('visibilitychange', function() {
    if (window.qrScanner) {
        if (document.hidden && window.qrScanner.isScanning) {
            window.qrScanner.stopScanning();
        }
    }
});

// Handle beforeunload to cleanup
window.addEventListener('beforeunload', function() {
    if (window.qrScanner && window.qrScanner.isScanning) {
        window.qrScanner.stopScanning();
    }
});
