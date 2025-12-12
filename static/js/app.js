let weeks = [];
let currentWeek = null;
let editMode = false;

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadWeeks();
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

async function loadWeeks() {
    try {
        const response = await fetch('/api/weeks');
        weeks = await response.json();
        renderWeeksList();
        populateFilters();
        updateWeekCount();
        
        if (weeks.length > 0 && !currentWeek) {
            showWelcome();
        }
    } catch (error) {
        showToast('Erro ao carregar semanas', 'error');
    }
}

function renderWeeksList(filteredWeeks = null) {
    const list = document.getElementById('weeksList');
    const weeksToRender = filteredWeeks || weeks;
    
    list.innerHTML = weeksToRender.map(week => `
        <li>
            <button onclick="selectWeek(${week.semana})" 
                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left
                ${currentWeek?.semana === week.semana 
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300' 
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'}">
                <span class="w-8 h-8 flex items-center justify-center rounded-lg text-sm font-semibold
                    ${currentWeek?.semana === week.semana 
                        ? 'bg-primary-500 text-white' 
                        : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'}">
                    ${week.semana}
                </span>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate">Semana ${week.semana}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 truncate">${week.unidadeCurricular}</p>
                </div>
            </button>
        </li>
    `).join('');
}

function populateFilters() {
    const ucSelect = document.getElementById('filterUC');
    const recursoSelect = document.getElementById('filterRecurso');
    
    const unidades = [...new Set(weeks.map(w => w.unidadeCurricular))];
    ucSelect.innerHTML = '<option value="">Todas as Unidades</option>' + 
        unidades.map(uc => `<option value="${uc}">${uc}</option>`).join('');
    
    const recursos = [...new Set(weeks.flatMap(w => w.recursos.split(',').map(r => r.trim())))];
    recursoSelect.innerHTML = '<option value="">Todos os Recursos</option>' + 
        recursos.sort().map(r => `<option value="${r}">${r}</option>`).join('');
}

function updateWeekCount() {
    document.getElementById('weekCount').textContent = weeks.length;
}

function setupEventListeners() {
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
            week.atividades.toLowerCase().includes(search) ||
            week.unidadeCurricular.toLowerCase().includes(search) ||
            week.capacidades.toLowerCase().includes(search) ||
            week.conhecimentos.toLowerCase().includes(search) ||
            week.recursos.toLowerCase().includes(search) ||
            `semana ${week.semana}`.includes(search);
        
        const matchesUC = !uc || week.unidadeCurricular === uc;
        const matchesRecurso = !recurso || week.recursos.includes(recurso);
        
        return matchesSearch && matchesUC && matchesRecurso;
    });
    
    renderWeeksList(filtered);
    updateWeekCount();
    document.getElementById('weekCount').textContent = filtered.length;
}

function selectWeek(semana) {
    currentWeek = weeks.find(w => w.semana === semana);
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
}

function showWeekContent() {
    document.getElementById('welcomeMessage').classList.add('hidden');
    document.getElementById('welcomeMessage').classList.remove('flex');
    document.getElementById('weekContent').classList.remove('hidden');
    
    document.getElementById('weekNumber').textContent = currentWeek.semana;
    document.getElementById('weekNumberTitle').textContent = currentWeek.semana;
    document.getElementById('weekUC').textContent = currentWeek.unidadeCurricular;
    document.getElementById('weekAtividades').textContent = currentWeek.atividades;
    document.getElementById('weekUnidade').textContent = currentWeek.unidadeCurricular;
    document.getElementById('weekCapacidades').textContent = currentWeek.capacidades;
    document.getElementById('weekConhecimentos').textContent = currentWeek.conhecimentos;
    
    const recursosContainer = document.getElementById('weekRecursos');
    const recursos = currentWeek.recursos.split(',').map(r => r.trim());
    recursosContainer.innerHTML = recursos.map(recurso => `
        <span class="inline-flex items-center gap-1 px-3 py-1.5 bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 rounded-full text-sm">
            <i class="fas fa-cube text-xs"></i>
            ${recurso}
        </span>
    `).join('');
}

function openModal(week = null) {
    editMode = !!week;
    const modal = document.getElementById('weekModal');
    const title = document.getElementById('modalTitle');
    
    title.textContent = editMode ? 'Editar Semana' : 'Nova Semana';
    
    if (week) {
        document.getElementById('formSemana').value = week.semana;
        document.getElementById('formSemana').disabled = true;
        document.getElementById('formAtividades').value = week.atividades;
        document.getElementById('formUnidade').value = week.unidadeCurricular;
        document.getElementById('formCapacidades').value = week.capacidades;
        document.getElementById('formConhecimentos').value = week.conhecimentos;
        document.getElementById('formRecursos').value = week.recursos;
    } else {
        document.getElementById('weekForm').reset();
        document.getElementById('formSemana').disabled = false;
        const maxSemana = Math.max(...weeks.map(w => w.semana), 0);
        document.getElementById('formSemana').value = maxSemana + 1;
    }
    
    modal.classList.remove('hidden');
}

function closeModal() {
    document.getElementById('weekModal').classList.add('hidden');
    document.getElementById('weekForm').reset();
}

function openConfirmModal() {
    document.getElementById('confirmModal').classList.remove('hidden');
    document.getElementById('confirmDeleteBtn').onclick = deleteCurrentWeek;
}

function closeConfirmModal() {
    document.getElementById('confirmModal').classList.add('hidden');
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const data = {
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
            response = await fetch(`/api/weeks/${currentWeek.semana}`, {
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
            
            if (editMode) {
                currentWeek = weeks.find(w => w.semana === data.semana);
                showWeekContent();
                showToast('Semana atualizada com sucesso!');
            } else {
                currentWeek = weeks.find(w => w.semana === data.semana);
                renderWeeksList();
                showWeekContent();
                showToast('Semana adicionada com sucesso!');
            }
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
        const response = await fetch(`/api/weeks/${currentWeek.semana}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            closeConfirmModal();
            currentWeek = null;
            await loadWeeks();
            showWelcome();
            showToast('Semana excluída com sucesso!');
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
