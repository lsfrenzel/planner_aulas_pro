let weeks = [];
let turmas = [];
let currentWeek = null;
let currentTurma = null;
let editMode = false;

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadTurmas();
    setupEventListeners();
});

function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
}

function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('-translate-x-full');
    overlay.classList.toggle('hidden');
}

function toggleExportMenu() {
    const menu = document.getElementById('exportMenu');
    menu.classList.toggle('hidden');
}

document.addEventListener('click', (e) => {
    const menu = document.getElementById('exportMenu');
    const button = e.target.closest('button');
    if (!e.target.closest('#exportMenu') && !button?.onclick?.toString().includes('toggleExportMenu')) {
        menu.classList.add('hidden');
    }
});

async function loadTurmas() {
    try {
        const response = await fetch('/api/turmas');
        const turmasAbertas = await response.json();
        
        turmas = turmasAbertas.map(t => ({ ...t, isEncerrada: false }));
        
        const select = document.getElementById('turmaSelect');
        select.innerHTML = '<option value="">Selecione uma turma...</option>' +
            turmasAbertas.map(t => `<option value="${t.id}">${t.nome}</option>`).join('');
        
        if (turmas.length === 0) {
            showNoTurmaState();
        } else {
            const savedTurmaId = localStorage.getItem('selectedTurmaId');
            if (savedTurmaId) {
                const savedTurma = turmas.find(t => t.id == savedTurmaId);
                if (savedTurma) {
                    select.value = savedTurmaId;
                    selectTurma(savedTurmaId);
                    return;
                }
            }
            showSelectTurmaState();
        }
    } catch (error) {
        showToast('Erro ao carregar turmas', 'error');
    }
}

function showNoTurmaState() {
    document.getElementById('noTurmaMessage').classList.remove('hidden');
    document.getElementById('turmaContent').classList.add('hidden');
    document.getElementById('selectTurmaMessage').classList.add('hidden');
    document.getElementById('selectTurmaMessage').classList.remove('flex');
    
    const mainContent = document.querySelector('main .flex-1');
    mainContent.innerHTML = `
        <div class="flex flex-col items-center justify-center h-full text-center">
            <div class="w-24 h-24 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center mb-6">
                <i class="fas fa-users text-4xl text-amber-500"></i>
            </div>
            <h3 class="text-2xl font-semibold text-gray-800 dark:text-white mb-2">Crie sua primeira Turma</h3>
            <p class="text-gray-500 dark:text-gray-400 max-w-md mb-6">Para comecar a planejar suas aulas, voce precisa criar uma turma primeiro. Cada turma tera seu proprio cronograma de semanas.</p>
            <a href="/turmas" class="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors font-medium">
                <i class="fas fa-plus"></i>
                Criar Turma
            </a>
        </div>
    `;
}

function showSelectTurmaState() {
    document.getElementById('noTurmaMessage').classList.add('hidden');
    document.getElementById('turmaContent').classList.add('hidden');
    document.getElementById('selectTurmaMessage').classList.remove('hidden');
    document.getElementById('selectTurmaMessage').classList.add('flex');
    document.getElementById('welcomeMessage').classList.add('hidden');
    document.getElementById('welcomeMessage').classList.remove('flex');
    document.getElementById('weekContent').classList.add('hidden');
}

async function selectTurma(turmaId) {
    if (!turmaId) {
        currentTurma = null;
        showSelectTurmaState();
        return;
    }
    
    currentTurma = turmas.find(t => t.id == turmaId);
    if (!currentTurma) return;
    
    localStorage.setItem('selectedTurmaId', turmaId);
    
    document.getElementById('noTurmaMessage').classList.add('hidden');
    document.getElementById('turmaContent').classList.remove('hidden');
    document.getElementById('selectTurmaMessage').classList.add('hidden');
    document.getElementById('selectTurmaMessage').classList.remove('flex');
    
    const turmaNameEl = document.getElementById('turmaName');
    if (currentTurma.isEncerrada || currentTurma.concluida) {
        turmaNameEl.innerHTML = `${currentTurma.nome} <span class="ml-2 px-2 py-0.5 bg-emerald-500 text-white text-xs rounded-full font-medium"><i class="fas fa-trophy mr-1"></i>Encerrada</span>`;
    } else {
        turmaNameEl.textContent = currentTurma.nome;
    }
    
    updateExportLinks();
    await loadWeeks();
}

function updateExportLinks() {
    if (currentTurma) {
        document.getElementById('exportJsonLink').href = `/api/export/json?turma_id=${currentTurma.id}`;
        document.getElementById('exportPdfLink').href = `/api/export/pdf?turma_id=${currentTurma.id}`;
    }
}

async function loadWeeks() {
    if (!currentTurma) return;
    
    try {
        const response = await fetch(`/api/weeks?turma_id=${currentTurma.id}`);
        weeks = await response.json();
        renderWeeksList();
        populateFilters();
        updateWeekCount();
        
        currentWeek = null;
        if (weeks.length > 0) {
            showWelcome();
        } else {
            showWelcome();
        }
    } catch (error) {
        showToast('Erro ao carregar semanas', 'error');
    }
}

function renderWeeksList(filteredWeeks = null) {
    const list = document.getElementById('weeksList');
    const weeksToRender = filteredWeeks || weeks;
    
    if (weeksToRender.length === 0) {
        list.innerHTML = `
            <li class="text-center py-4">
                <p class="text-sm text-gray-500 dark:text-gray-400">Nenhuma semana cadastrada.</p>
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Clique em "Nova Semana" para adicionar.</p>
            </li>
        `;
        return;
    }
    
    list.innerHTML = weeksToRender.map(week => `
        <li>
            <button onclick="selectWeek(${week.id})" 
                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left
                ${currentWeek?.id === week.id 
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300' 
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'}">
                <span class="w-8 h-8 flex items-center justify-center rounded-lg text-sm font-semibold
                    ${currentWeek?.id === week.id 
                        ? 'bg-primary-500 text-white' 
                        : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'}">
                    ${week.semana}
                </span>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate">Semana ${week.semana}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 truncate">${week.unidadeCurricular}</p>
                </div>
                ${week.completed ? '<i class="fas fa-check-circle text-green-500"></i>' : ''}
            </button>
        </li>
    `).join('');
}

function populateFilters() {
    const ucSelect = document.getElementById('filterUC');
    const recursoSelect = document.getElementById('filterRecurso');
    
    const unidades = [...new Set(weeks.map(w => w.unidadeCurricular).filter(u => u))];
    ucSelect.innerHTML = '<option value="">Todas as Unidades</option>' + 
        unidades.map(uc => `<option value="${uc}">${uc}</option>`).join('');
    
    const recursos = [...new Set(weeks.flatMap(w => (w.recursos || '').split(',').map(r => r.trim())).filter(r => r))];
    recursoSelect.innerHTML = '<option value="">Todos os Recursos</option>' + 
        recursos.sort().map(r => `<option value="${r}">${r}</option>`).join('');
}

function updateWeekCount() {
    document.getElementById('weekCount').textContent = weeks.length;
}

function setupEventListeners() {
    document.getElementById('turmaSelect').addEventListener('change', (e) => {
        selectTurma(e.target.value);
    });
    document.getElementById('searchInput').addEventListener('input', filterWeeks);
    document.getElementById('filterUC').addEventListener('change', filterWeeks);
    document.getElementById('filterRecurso').addEventListener('change', filterWeeks);
    document.getElementById('addWeekBtn').addEventListener('click', () => openModal());
    document.getElementById('editWeekBtn').addEventListener('click', () => openModal(currentWeek));
    document.getElementById('deleteWeekBtn').addEventListener('click', () => openConfirmModal());
    document.getElementById('weekForm').addEventListener('submit', handleFormSubmit);
}

function filterWeeks() {
    const search = document.getElementById('searchInput').value.toLowerCase();
    const uc = document.getElementById('filterUC').value;
    const recurso = document.getElementById('filterRecurso').value;
    
    const filtered = weeks.filter(week => {
        const matchesSearch = !search || 
            (week.atividades || '').toLowerCase().includes(search) ||
            (week.unidadeCurricular || '').toLowerCase().includes(search) ||
            (week.capacidades || '').toLowerCase().includes(search) ||
            (week.conhecimentos || '').toLowerCase().includes(search) ||
            (week.recursos || '').toLowerCase().includes(search) ||
            `semana ${week.semana}`.includes(search);
        
        const matchesUC = !uc || week.unidadeCurricular === uc;
        const matchesRecurso = !recurso || (week.recursos || '').includes(recurso);
        
        return matchesSearch && matchesUC && matchesRecurso;
    });
    
    renderWeeksList(filtered);
    document.getElementById('weekCount').textContent = filtered.length;
}

function selectWeek(weekId) {
    currentWeek = weeks.find(w => w.id === weekId);
    if (!currentWeek) return;
    
    renderWeeksList();
    showWeekContent();
    
    if (window.innerWidth < 1024) {
        toggleSidebar();
    }
}

function showWelcome() {
    document.getElementById('welcomeMessage').classList.remove('hidden');
    document.getElementById('welcomeMessage').classList.add('flex');
    document.getElementById('weekContent').classList.add('hidden');
    document.getElementById('selectTurmaMessage').classList.add('hidden');
    document.getElementById('selectTurmaMessage').classList.remove('flex');
}

function showWeekContent() {
    document.getElementById('welcomeMessage').classList.add('hidden');
    document.getElementById('welcomeMessage').classList.remove('flex');
    document.getElementById('weekContent').classList.remove('hidden');
    document.getElementById('selectTurmaMessage').classList.add('hidden');
    document.getElementById('selectTurmaMessage').classList.remove('flex');
    
    document.getElementById('weekNumber').textContent = currentWeek.semana;
    document.getElementById('weekNumberTitle').textContent = currentWeek.semana;
    document.getElementById('weekUC').textContent = currentWeek.unidadeCurricular || 'Sem unidade curricular';
    document.getElementById('weekAtividades').textContent = currentWeek.atividades || '-';
    document.getElementById('weekUnidade').textContent = currentWeek.unidadeCurricular || '-';
    document.getElementById('weekCapacidades').textContent = currentWeek.capacidades || '-';
    document.getElementById('weekConhecimentos').textContent = currentWeek.conhecimentos || '-';
    
    const recursosContainer = document.getElementById('weekRecursos');
    const recursos = (currentWeek.recursos || '').split(',').map(r => r.trim()).filter(r => r);
    if (recursos.length > 0) {
        recursosContainer.innerHTML = recursos.map(recurso => `
            <span class="inline-flex items-center gap-1 px-3 py-1.5 bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 rounded-full text-sm">
                <i class="fas fa-cube text-xs"></i>
                ${recurso}
            </span>
        `).join('');
    } else {
        recursosContainer.innerHTML = '<span class="text-gray-500 dark:text-gray-400 text-sm">Nenhum recurso especificado</span>';
    }
}

function openModal(week = null) {
    if (!currentTurma) {
        showToast('Selecione uma turma primeiro', 'error');
        return;
    }
    
    editMode = !!week;
    const modal = document.getElementById('weekModal');
    const title = document.getElementById('modalTitle');
    
    title.textContent = editMode ? 'Editar Semana' : 'Nova Semana';
    
    if (week) {
        document.getElementById('formSemana').value = week.semana;
        document.getElementById('formSemana').disabled = true;
        document.getElementById('formAtividades').value = week.atividades || '';
        document.getElementById('formUnidade').value = week.unidadeCurricular || '';
        document.getElementById('formCapacidades').value = week.capacidades || '';
        document.getElementById('formConhecimentos').value = week.conhecimentos || '';
        document.getElementById('formRecursos').value = week.recursos || '';
    } else {
        document.getElementById('weekForm').reset();
        document.getElementById('formSemana').disabled = false;
        const maxSemana = Math.max(...weeks.map(w => w.semana), 0);
        document.getElementById('formSemana').value = maxSemana + 1;
    }
    
    modal.classList.remove('hidden');
    
    setTimeout(() => {
        if (editMode) {
            document.getElementById('formAtividades').focus();
        } else {
            document.getElementById('formSemana').focus();
        }
    }, 100);
}

function closeModal() {
    document.getElementById('weekModal').classList.add('hidden');
    document.getElementById('weekForm').reset();
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const weekModal = document.getElementById('weekModal');
        const confirmModal = document.getElementById('confirmModal');
        if (!weekModal.classList.contains('hidden')) {
            closeModal();
        } else if (!confirmModal.classList.contains('hidden')) {
            closeConfirmModal();
        }
    }
});

function openConfirmModal() {
    document.getElementById('confirmModal').classList.remove('hidden');
    document.getElementById('confirmDeleteBtn').onclick = deleteCurrentWeek;
}

function closeConfirmModal() {
    document.getElementById('confirmModal').classList.add('hidden');
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (!currentTurma) {
        showToast('Selecione uma turma primeiro', 'error');
        return;
    }
    
    const data = {
        turma_id: currentTurma.id,
        semana: parseInt(document.getElementById('formSemana').value),
        atividades: document.getElementById('formAtividades').value,
        unidadeCurricular: document.getElementById('formUnidade').value,
        capacidades: document.getElementById('formCapacidades').value,
        conhecimentos: document.getElementById('formConhecimentos').value,
        recursos: document.getElementById('formRecursos').value
    };
    
    try {
        let response;
        if (editMode) {
            response = await fetch(`/api/weeks/${currentWeek.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch('/api/weeks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            closeModal();
            await loadWeeks();
            
            const savedWeek = weeks.find(w => w.semana === data.semana);
            if (savedWeek) {
                currentWeek = savedWeek;
                renderWeeksList();
                showWeekContent();
            }
            
            showToast(editMode ? 'Semana atualizada com sucesso!' : 'Semana adicionada com sucesso!');
        } else {
            const error = await response.json();
            showToast(error.error || 'Erro ao salvar semana', 'error');
        }
    } catch (error) {
        showToast('Erro ao salvar semana', 'error');
    }
}

async function deleteCurrentWeek() {
    if (!currentWeek) return;
    
    try {
        const response = await fetch(`/api/weeks/${currentWeek.id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            closeConfirmModal();
            currentWeek = null;
            await loadWeeks();
            showWelcome();
            showToast('Semana excluida com sucesso!');
        } else {
            showToast('Erro ao excluir semana', 'error');
        }
    } catch (error) {
        showToast('Erro ao excluir semana', 'error');
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const icon = document.getElementById('toastIcon');
    const msg = document.getElementById('toastMessage');
    
    msg.textContent = message;
    icon.className = type === 'success' 
        ? 'fas fa-check-circle text-green-400' 
        : 'fas fa-exclamation-circle text-red-400';
    
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}
