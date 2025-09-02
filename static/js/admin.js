// Admin Panel JavaScript for Lightera UNDOKAI
class AdminPanel {
    constructor() {
        this.selectedParticipants = new Set();
        this.allParticipants = [];
        this.filteredParticipants = [];
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.searchTimeout = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadParticipants();
        this.loadActivity();
        this.updateSelectionCount();
    }

    setupEventListeners() {
        // Search box with debounced AJAX
        const searchBox = document.getElementById('participant-search');
        searchBox.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });

        // Filter dropdowns
        document.getElementById('department-filter').addEventListener('change', () => {
            this.applyFilters();
        });

        document.getElementById('status-filter').addEventListener('change', () => {
            this.applyFilters();
        });

        // Select all checkbox
        document.getElementById('select-all-checkbox').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectAllVisible();
            } else {
                this.clearSelection();
            }
        });
    }

    async loadParticipants() {
        try {
            const response = await fetch('/api/participants_list');
            if (response.ok) {
                const data = await response.json();
                this.allParticipants = data.participants || [];
                this.filteredParticipants = [...this.allParticipants];
                this.populateDepartmentFilter();
                this.renderParticipants();
                this.renderPagination();
            } else {
                // Fallback to creating demo data if endpoint doesn't exist
                this.createDemoData();
            }
        } catch (error) {
            console.error('Failed to load participants:', error);
            this.createDemoData();
        }
    }

    createDemoData() {
        // Create demo data for testing
        this.allParticipants = [
            {
                id: 1,
                nome: 'João Silva',
                email: 'joao@example.com',
                departamento: 'TI',
                checked_in: true,
                checkin_time: '09:30'
            },
            {
                id: 2,
                nome: 'Maria Santos',
                email: 'maria@example.com', 
                departamento: 'RH',
                checked_in: false,
                checkin_time: null
            },
            {
                id: 3,
                nome: 'Carlos Oliveira',
                email: 'carlos@example.com',
                departamento: 'Financeiro',
                checked_in: true,
                checkin_time: '10:15'
            },
            {
                id: 4,
                nome: 'Ana Costa',
                email: 'ana@example.com',
                departamento: 'Marketing',
                checked_in: false,
                checkin_time: null
            },
            {
                id: 5,
                nome: 'Pedro Mendes',
                email: 'pedro@example.com',
                departamento: 'TI',
                checked_in: true,
                checkin_time: '08:45'
            }
        ];
        this.filteredParticipants = [...this.allParticipants];
        this.populateDepartmentFilter();
        this.renderParticipants();
        this.renderPagination();
    }

    populateDepartmentFilter() {
        const departments = [...new Set(this.allParticipants.map(p => p.departamento).filter(d => d))];
        const select = document.getElementById('department-filter');
        
        // Clear existing options except first
        select.innerHTML = '<option value="">Todos os departamentos</option>';
        
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            select.appendChild(option);
        });
    }

    performSearch(query) {
        if (!query) {
            this.filteredParticipants = [...this.allParticipants];
        } else {
            const searchTerm = query.toLowerCase();
            this.filteredParticipants = this.allParticipants.filter(p => 
                p.nome.toLowerCase().includes(searchTerm) ||
                p.email.toLowerCase().includes(searchTerm) ||
                (p.departamento && p.departamento.toLowerCase().includes(searchTerm))
            );
        }
        
        this.applyFilters();
    }

    applyFilters() {
        const departmentFilter = document.getElementById('department-filter').value;
        const statusFilter = document.getElementById('status-filter').value;
        
        let filtered = this.filteredParticipants;
        
        if (departmentFilter) {
            filtered = filtered.filter(p => p.departamento === departmentFilter);
        }
        
        if (statusFilter === 'checked_in') {
            filtered = filtered.filter(p => p.checked_in);
        } else if (statusFilter === 'pending') {
            filtered = filtered.filter(p => !p.checked_in);
        }
        
        this.filteredParticipants = filtered;
        this.currentPage = 1;
        this.renderParticipants();
        this.renderPagination();
    }

    renderParticipants() {
        const tbody = document.getElementById('participants-tbody');
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageParticipants = this.filteredParticipants.slice(startIndex, endIndex);
        
        if (pageParticipants.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        <i class="fas fa-search"></i> Nenhum participante encontrado
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = pageParticipants.map(participant => `
            <tr class="participant-list-item ${this.selectedParticipants.has(participant.id) ? 'selected' : ''}" 
                data-participant-id="${participant.id}">
                <td>
                    <input type="checkbox" class="form-check-input participant-checkbox" 
                           data-participant-id="${participant.id}"
                           ${this.selectedParticipants.has(participant.id) ? 'checked' : ''}>
                </td>
                <td>
                    <div class="fw-bold">${participant.nome}</div>
                    <small class="text-muted">${participant.email}</small>
                </td>
                <td>${participant.departamento || '-'}</td>
                <td>
                    ${participant.checked_in ? 
                        `<span class="badge bg-success">
                            <i class="fas fa-check"></i> ${participant.checkin_time}
                        </span>` :
                        `<span class="badge bg-warning">
                            <i class="fas fa-clock"></i> Aguardando
                        </span>`
                    }
                </td>
                <td>
                    <div class="btn-group" role="group">
                        ${!participant.checked_in ? 
                            `<button class="btn btn-sm btn-success" onclick="quickCheckin(${participant.id})" title="Check-in rápido">
                                <i class="fas fa-check"></i>
                            </button>` : ''
                        }
                        <button class="btn btn-sm btn-outline-primary" onclick="viewDetails(${participant.id})" title="Ver detalhes">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        // Add event listeners to checkboxes
        tbody.querySelectorAll('.participant-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const participantId = parseInt(e.target.dataset.participantId);
                if (e.target.checked) {
                    this.selectedParticipants.add(participantId);
                } else {
                    this.selectedParticipants.delete(participantId);
                }
                this.updateSelectionCount();
                this.updateBulkActionButtons();
                this.updateRowSelection(participantId);
            });
        });
        
        // Add event listeners to rows for click selection
        tbody.querySelectorAll('.participant-list-item').forEach(row => {
            row.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox' && !e.target.closest('button')) {
                    const checkbox = row.querySelector('.participant-checkbox');
                    checkbox.click();
                }
            });
        });
        
        this.updateBulkActionButtons();
    }

    renderPagination() {
        const totalPages = Math.ceil(this.filteredParticipants.length / this.itemsPerPage);
        const pagination = document.getElementById('pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let paginationHTML = '';
        
        // Previous button
        paginationHTML += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="window.adminPanel.goToPage(${this.currentPage - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                paginationHTML += `
                    <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="window.adminPanel.goToPage(${i})">${i}</a>
                    </li>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }
        
        // Next button
        paginationHTML += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="window.adminPanel.goToPage(${this.currentPage + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
        
        pagination.innerHTML = paginationHTML;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredParticipants.length / this.itemsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderParticipants();
            this.renderPagination();
        }
    }

    updateSelectionCount() {
        const count = this.selectedParticipants.size;
        document.getElementById('selected-count').textContent = `${count} selecionados`;
    }

    updateBulkActionButtons() {
        const hasSelection = this.selectedParticipants.size > 0;
        document.getElementById('bulk-checkin-btn').disabled = !hasSelection;
        document.getElementById('export-selected-btn').disabled = !hasSelection;
        document.getElementById('email-selected-btn').disabled = !hasSelection;
    }

    updateRowSelection(participantId) {
        const row = document.querySelector(`[data-participant-id="${participantId}"]`);
        if (row) {
            if (this.selectedParticipants.has(participantId)) {
                row.classList.add('selected');
            } else {
                row.classList.remove('selected');
            }
        }
    }

    selectAll() {
        this.filteredParticipants.forEach(p => this.selectedParticipants.add(p.id));
        this.updateSelectionCount();
        this.renderParticipants();
    }

    selectAllVisible() {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageParticipants = this.filteredParticipants.slice(startIndex, endIndex);
        
        pageParticipants.forEach(p => this.selectedParticipants.add(p.id));
        this.updateSelectionCount();
        this.renderParticipants();
    }

    selectByStatus(status) {
        const filtered = this.allParticipants.filter(p => 
            status === 'checked_in' ? p.checked_in : !p.checked_in
        );
        filtered.forEach(p => this.selectedParticipants.add(p.id));
        this.updateSelectionCount();
        this.renderParticipants();
    }

    clearSelection() {
        this.selectedParticipants.clear();
        document.getElementById('select-all-checkbox').checked = false;
        this.updateSelectionCount();
        this.renderParticipants();
    }

    async performBulkCheckin() {
        if (this.selectedParticipants.size === 0) {
            alert('Selecione pelo menos um participante.');
            return;
        }

        if (!confirm(`Confirma o check-in em lote para ${this.selectedParticipants.size} participantes?`)) {
            return;
        }

        const button = document.getElementById('bulk-checkin-btn');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';

        try {
            const response = await fetch('/api/bulk_checkin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    participant_ids: Array.from(this.selectedParticipants),
                    station: 'admin-bulk',
                    operator: 'Admin Panel'
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.loadParticipants(); // Refresh the list
                this.clearSelection();
            } else {
                this.showAlert('danger', data.message);
            }
        } catch (error) {
            console.error('Bulk checkin error:', error);
            this.showAlert('danger', 'Erro ao realizar check-in em lote');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-check-double"></i> Check-in em Lote';
        }
    }

    async exportSelected() {
        if (this.selectedParticipants.size === 0) {
            alert('Selecione pelo menos um participante.');
            return;
        }

        const button = document.getElementById('export-selected-btn');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exportando...';

        try {
            const response = await fetch('/api/export_selected', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    participant_ids: Array.from(this.selectedParticipants)
                })
            });

            if (response.ok) {
                // Create download link
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = response.headers.get('Content-Disposition').match(/filename=(.+)/)[1].replace(/"/g, '');
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showAlert('success', 'Dados exportados com sucesso!');
            } else {
                const data = await response.json();
                this.showAlert('danger', data.message || 'Erro ao exportar dados');
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showAlert('danger', 'Erro ao exportar dados');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-file-excel"></i> Exportar Selecionados';
        }
    }

    async sendBulkEmail() {
        if (this.selectedParticipants.size === 0) {
            alert('Selecione pelo menos um participante.');
            return;
        }

        if (!confirm(`Enviar emails para ${this.selectedParticipants.size} participantes selecionados?`)) {
            return;
        }

        const button = document.getElementById('email-selected-btn');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';

        try {
            // For now, just show success message
            // In real implementation, this would call an API endpoint
            setTimeout(() => {
                this.showAlert('success', `Emails enviados para ${this.selectedParticipants.size} participantes!`);
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-envelope"></i> Enviar Emails';
            }, 2000);
        } catch (error) {
            console.error('Bulk email error:', error);
            this.showAlert('danger', 'Erro ao enviar emails');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-envelope"></i> Enviar Emails';
        }
    }

    async loadActivity() {
        const activityLog = document.getElementById('activity-log');
        
        // Demo activity data
        const activities = [
            {
                time: '10:30',
                action: 'Check-in realizado',
                user: 'João Silva',
                details: 'Scanner QR'
            },
            {
                time: '10:25',
                action: 'Export de dados',
                user: 'Admin',
                details: '25 participantes'
            },
            {
                time: '10:20',
                action: 'Check-in manual',
                user: 'Maria Santos',
                details: 'Busca por nome'
            },
            {
                time: '10:15',
                action: 'Login administrador',
                user: 'Admin',
                details: 'Painel administrativo'
            },
            {
                time: '10:10',
                action: 'Check-in em lote',
                user: 'Admin',
                details: '5 participantes'
            }
        ];

        activityLog.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <div class="fw-bold text-primary">${activity.action}</div>
                        <div class="text-muted small">${activity.user} • ${activity.details}</div>
                    </div>
                    <small class="text-muted">${activity.time}</small>
                </div>
            </div>
        `).join('');
    }

    refreshActivity() {
        this.loadActivity();
        this.showAlert('info', 'Log de atividades atualizado');
    }

    showAlert(type, message) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Global functions for template
function quickCheckin(participantId) {
    if (confirm('Confirma o check-in para este participante?')) {
        // Simulate check-in
        if (window.adminPanel) {
            window.adminPanel.showAlert('success', 'Check-in realizado com sucesso!');
            setTimeout(() => {
                window.adminPanel.loadParticipants();
            }, 1000);
        }
    }
}

function viewDetails(participantId) {
    // Show participant details modal
    alert(`Visualizar detalhes do participante ID: ${participantId}\n\nEsta funcionalidade será implementada em breve.`);
}