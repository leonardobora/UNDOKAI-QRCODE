// Participant Search JavaScript for Lightera BUNDOKAI
class ParticipantSearch {
    constructor() {
        this.searchTimeout = null;
        this.selectedParticipant = null;
        this.recentCheckins = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadRecentCheckins();
    }

    setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        
        // Search input with debouncing
        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                this.hideResults();
                return;
            }
            
            this.searchTimeout = setTimeout(() => {
                this.searchParticipants(query);
            }, 300);
        });

        // Handle Enter key in search
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const firstResult = document.querySelector('.search-result-item');
                if (firstResult && !firstResult.classList.contains('no-results')) {
                    firstResult.click();
                }
            }
        });

        // Clear search
        document.getElementById('searchInput').addEventListener('focus', () => {
            this.clearSearch();
        });

        // Modal event listeners
        document.getElementById('confirm-checkin').addEventListener('click', () => {
            this.performManualCheckin();
        });
    }

    searchParticipants(query) {
        this.showLoading();
        
        fetch(`/api/search_participant?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(participants => {
                this.hideLoading();
                this.displayResults(participants);
            })
            .catch(error => {
                this.hideLoading();
                console.error('Search error:', error);
                this.showError('Erro ao buscar participantes. Tente novamente.');
            });
    }

    displayResults(participants) {
        const resultsContainer = document.getElementById('search-results');
        const resultsList = document.getElementById('results-list');
        const noResults = document.getElementById('no-results');
        
        if (participants.length === 0) {
            resultsContainer.style.display = 'none';
            noResults.style.display = 'block';
            return;
        }
        
        noResults.style.display = 'none';
        resultsContainer.style.display = 'block';
        
        resultsList.innerHTML = participants.map(participant => `
            <div class="list-group-item search-result-item" 
                 onclick="searchInstance.selectParticipant(${participant.id})"
                 data-participant-id="${participant.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${participant.nome}</h6>
                        <p class="mb-1 text-muted">${participant.email}</p>
                        <small class="text-muted">
                            ${participant.departamento ? `Departamento: ${participant.departamento} • ` : ''}
                            Dependentes: ${participant.dependents_count} • 
                            QR: <code>${participant.qr_code}</code>
                        </small>
                    </div>
                    <div class="text-end">
                        ${participant.checked_in ? 
                            `<span class="badge bg-success">Check-in: ${participant.checkin_time}</span>` :
                            `<span class="badge bg-warning">Aguardando</span>`
                        }
                    </div>
                </div>
            </div>
        `).join('');
    }

    selectParticipant(participantId) {
        // Find participant data
        const participants = Array.from(document.querySelectorAll('.search-result-item')).map(item => {
            return parseInt(item.dataset.participantId);
        });
        
        fetch(`/api/participant/${participantId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.selectedParticipant = data.participant;
                    this.showConfirmationModal(data.participant);
                } else {
                    alert('Erro ao carregar dados do participante.');
                }
            })
            .catch(error => {
                console.error('Error loading participant:', error);
                alert('Erro ao carregar dados do participante.');
            });
    }

    showConfirmationModal(participant) {
        const modal = document.getElementById('confirmModal');
        const detailsContainer = document.getElementById('participant-details');
        
        detailsContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h6><strong>Nome:</strong></h6>
                    <p>${participant.nome}</p>
                    
                    <h6><strong>Email:</strong></h6>
                    <p>${participant.email}</p>
                    
                    ${participant.telefone ? `
                        <h6><strong>Telefone:</strong></h6>
                        <p>${participant.telefone}</p>
                    ` : ''}
                    
                    ${participant.departamento ? `
                        <h6><strong>Departamento:</strong></h6>
                        <p>${participant.departamento}</p>
                    ` : ''}
                    
                    <h6><strong>QR Code:</strong></h6>
                    <p><code class="fs-6">${participant.qr_code}</code></p>
                    
                    <h6><strong>Dependentes:</strong></h6>
                    <p>${participant.dependents_count} pessoa(s)</p>
                    
                    ${participant.dependents && participant.dependents.length > 0 ? `
                        <h6><strong>Lista de Dependentes:</strong></h6>
                        <ul class="list-unstyled">
                            ${participant.dependents.map(dep => `
                                <li><i class="fas fa-user"></i> ${dep.nome} ${dep.idade ? `(${dep.idade} anos)` : ''}</li>
                            `).join('')}
                        </ul>
                    ` : ''}
                    
                    ${participant.checked_in ? `
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i>
                            <strong>Atenção:</strong> Este participante já fez check-in às ${participant.checkin_time}.
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Disable confirm button if already checked in
        const confirmBtn = document.getElementById('confirm-checkin');
        if (participant.checked_in) {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> Já Fez Check-in';
        } else {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> Confirmar Check-in';
        }
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    performManualCheckin() {
        if (!this.selectedParticipant || this.selectedParticipant.checked_in) {
            return;
        }
        
        const confirmBtn = document.getElementById('confirm-checkin');
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
        
        const requestData = {
            participant_id: this.selectedParticipant.id,
            station: 'manual-search',
            operator: 'Busca Manual'
        };
        
        fetch('/api/manual_checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> Confirmar Check-in';
            
            if (data.success) {
                // Close confirmation modal
                const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
                confirmModal.hide();
                
                // Add to recent checkins
                this.addRecentCheckin({
                    time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
                    participant: this.selectedParticipant.nome,
                    departamento: this.selectedParticipant.departamento || 'N/A',
                    dependents: this.selectedParticipant.dependents_count,
                    status: 'Manual'
                });
                
                // Show success modal
                this.showSuccessModal(data.participant);
                
                // Clear search
                this.clearSearch();
                
            } else {
                alert('Erro no check-in: ' + data.message);
            }
        })
        .catch(error => {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> Confirmar Check-in';
            console.error('Check-in error:', error);
            alert('Erro ao realizar check-in. Tente novamente.');
        });
    }

    showSuccessModal(participant) {
        const modal = document.getElementById('successModal');
        const detailsContainer = document.getElementById('success-details');
        
        detailsContainer.innerHTML = `
            <div class="text-center mb-3">
                <i class="fas fa-check-circle fa-4x text-success"></i>
            </div>
            <h5 class="text-center mb-3">Check-in Manual Realizado!</h5>
            <div class="card">
                <div class="card-body">
                    <p><strong>Participante:</strong> ${participant.nome}</p>
                    <p><strong>Horário:</strong> ${participant.checkin_time}</p>
                    <p><strong>Método:</strong> Busca Manual</p>
                </div>
            </div>
        `;
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            bsModal.hide();
        }, 3000);
    }

    addRecentCheckin(checkin) {
        this.recentCheckins.unshift(checkin);
        if (this.recentCheckins.length > 10) {
            this.recentCheckins.pop();
        }
        this.updateRecentCheckinsDisplay();
        
        // Save to localStorage
        localStorage.setItem('recentManualCheckins', JSON.stringify(this.recentCheckins));
    }

    updateRecentCheckinsDisplay() {
        const tbody = document.getElementById('manual-checkins-tbody');
        
        if (this.recentCheckins.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        Nenhum check-in manual realizado ainda
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = this.recentCheckins.map(checkin => `
            <tr>
                <td>${checkin.time}</td>
                <td>${checkin.participant}</td>
                <td>${checkin.departamento}</td>
                <td class="text-center">${checkin.dependents}</td>
                <td><span class="badge bg-info">${checkin.status}</span></td>
            </tr>
        `).join('');
    }

    loadRecentCheckins() {
        const saved = localStorage.getItem('recentManualCheckins');
        if (saved) {
            this.recentCheckins = JSON.parse(saved);
            this.updateRecentCheckinsDisplay();
        }
    }

    showLoading() {
        document.getElementById('search-loading').style.display = 'block';
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('no-results').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('search-loading').style.display = 'none';
    }

    hideResults() {
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('no-results').style.display = 'none';
        document.getElementById('search-loading').style.display = 'none';
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert error at the top of the search section
        const searchInput = document.getElementById('searchInput');
        searchInput.parentNode.insertBefore(errorDiv, searchInput.nextSibling);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    clearSearch() {
        document.getElementById('searchInput').value = '';
        this.hideResults();
        this.selectedParticipant = null;
    }
}

// Global functions for template
function clearSearch() {
    if (window.searchInstance) {
        window.searchInstance.clearSearch();
    }
}

// Initialize search when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.searchInstance = new ParticipantSearch();
});

// Offline support using Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Handle online/offline status
window.addEventListener('online', function() {
    console.log('Connection restored');
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'alert alert-success alert-dismissible fade show position-fixed';
    statusIndicator.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
    statusIndicator.innerHTML = `
        <i class="fas fa-wifi"></i> Conexão restaurada
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(statusIndicator);
    
    setTimeout(() => {
        if (statusIndicator.parentNode) {
            statusIndicator.remove();
        }
    }, 3000);
});

window.addEventListener('offline', function() {
    console.log('Connection lost - using offline mode');
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'alert alert-warning alert-dismissible fade show position-fixed';
    statusIndicator.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
    statusIndicator.innerHTML = `
        <i class="fas fa-wifi-slash"></i> Modo offline ativo
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(statusIndicator);
});
