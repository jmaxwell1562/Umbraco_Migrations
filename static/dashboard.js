/* Dashboard JavaScript */

const API_BASE = '/api';
let currentSiteData = null;
let auditRunning = false;

// DOM Elements
const auditForm = document.getElementById('auditForm');
const submitBtn = document.getElementById('submitBtn');
const progressContainer = document.getElementById('progressContainer');
const summaryContainer = document.getElementById('summaryContainer');
const readinessContainer = document.getElementById('readinessContainer');
const queueAContainer = document.getElementById('queueAContainer');
const queueBContainer = document.getElementById('queueBContainer');
const actionsContainer = document.getElementById('actionsContainer');
const reportLinksContainer = document.getElementById('reportLinksContainer');
const emptyState = document.getElementById('emptyState');
const errorMessage = document.getElementById('errorMessage');
const toast = document.getElementById('toast');
const statusText = document.getElementById('statusText');
const headerStatus = document.getElementById('headerStatus');
const runStateBadge = document.getElementById('runStateBadge');
const latestReportCard = document.getElementById('latestReportCard');
const previousReportCard = document.getElementById('previousReportCard');
const previousReportLink = document.getElementById('previousReportLink');
const previousReportStats = document.getElementById('previousReportStats');
const latestReportLink = document.getElementById('latestReportLink');
const latestReportMeta = document.getElementById('latestReportMeta');
const siteNameInput = document.getElementById('siteName');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    auditForm.addEventListener('submit', handleFormSubmit);
    siteNameInput.addEventListener('change', handleSiteSelectionChange);
    siteNameInput.addEventListener('blur', handleSiteSelectionChange);
});

async function handleSiteSelectionChange() {
    const siteName = siteNameInput.value.trim();
    if (!siteName || auditRunning) {
        return;
    }

    await loadReportData(siteName);
}

function resetResultsView() {
    reportLinksContainer.classList.add('hidden');
    queueAContainer.classList.add('hidden');
    if (latestReportCard) {
        latestReportCard.classList.add('hidden');
    }
    if (previousReportCard) {
        previousReportCard.classList.add('hidden');
    }
    if (latestReportLink) {
        latestReportLink.href = '#';
        latestReportLink.classList.remove('is-disabled');
    }
    if (latestReportMeta) {
        latestReportMeta.textContent = '';
    }
    if (previousReportLink) {
        previousReportLink.href = '#';
        previousReportLink.textContent = 'Previous report not available yet';
        previousReportLink.classList.add('is-disabled');
    }
    if (previousReportStats) {
        previousReportStats.innerHTML = '<p class="placeholder">Run this site again to compare against a previous report.</p>';
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    setTimeout(() => {
        errorMessage.classList.add('hidden');
    }, 5000);
}

function showToast(message) {
    toast.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function setStatus(text, type = 'online') {
    statusText.textContent = text;
    headerStatus.querySelector('.status-indicator').className = `status-indicator ${type}`;
}

function setRunButtonState(state, label) {
    const submitText = document.getElementById('submitText');
    const spinner = document.getElementById('spinner');

    submitBtn.classList.remove('is-running', 'is-success', 'is-error');
    if (state !== 'idle') {
        submitBtn.classList.add(`is-${state}`);
    }

    submitText.textContent = label;
    spinner.classList.toggle('hidden', state !== 'running');

    if (runStateBadge) {
        runStateBadge.className = `run-state-badge state-${state}`;
        if (state === 'running') {
            runStateBadge.textContent = 'Status: Running';
        } else if (state === 'success') {
            runStateBadge.textContent = 'Status: Complete';
        } else if (state === 'error') {
            runStateBadge.textContent = 'Status: Error';
        } else {
            runStateBadge.textContent = 'Status: Ready';
        }
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();

    if (auditRunning) return;

    const formData = new FormData(auditForm);
    const data = {
        site_name: formData.get('site_name'),
        source_url: formData.get('source_url'),
        test_url: formData.get('test_url'),
        run_mode: formData.get('run_mode'),
        test_scope: formData.get('test_scope'),
        test_allowlist: formData.get('test_allowlist'),
        test_allowlist_file: formData.get('test_allowlist_file'),
        report_folder: formData.get('report_folder'),
    };

    // Validate
    if (!data.site_name || !data.test_url) {
        showError('Site name and test URL are required');
        return;
    }

    auditRunning = true;
    submitBtn.disabled = true;
    setRunButtonState('running', 'Running Audit...');
    resetResultsView();

    setStatus('Running audit...', 'busy');
    showProgress();

    try {
        // Start audit
        const response = await fetch(`${API_BASE}/audit/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Audit run failed');
        }

        const result = await response.json();

        // Load report
        await loadReportData(data.site_name, data);

        setStatus('Ready', 'online');
        setRunButtonState('success', 'Audit Complete');
        showToast('✓ Audit completed');

    } catch (error) {
        setStatus('Error', 'error');
        setRunButtonState('error', 'Run Failed');
        showError(`Error: ${error.message}`);
    } finally {
        auditRunning = false;
        submitBtn.disabled = false;
        setTimeout(() => setRunButtonState('idle', 'Start Audit'), 1200);
        hideProgress();
    }
}

function showProgress() {
    progressContainer.classList.remove('hidden');
    emptyState.classList.add('hidden');

    // Animate progress
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    let width = 0;

    const interval = setInterval(() => {
        width += Math.random() * 30;
        if (width > 90) width = 90;
        progressFill.style.width = width + '%';
        progressText.textContent = `Progress: ${Math.round(width)}%`;
    }, 500);

    // Complete progress
    setTimeout(() => {
        clearInterval(interval);
        progressFill.style.width = '100%';
        progressText.textContent = 'Processing results...';
    }, 5000);
}

function hideProgress() {
    setTimeout(() => {
        progressContainer.classList.add('hidden');
    }, 1000);
}

async function loadReportData(siteName, auditData) {
    try {
        const response = await fetch(`${API_BASE}/reports/${encodeURIComponent(siteName)}`);
        if (!response.ok) throw new Error('Failed to load report');

        const data = await response.json();
        currentSiteData = data;

        if (data.latest && data.latest.audit_summary) {
            displayResults(data.latest, data);
        } else {
            resetResultsView();
            emptyState.classList.remove('hidden');
            showError('No audit results found');
        }

    } catch (error) {
        resetResultsView();
        emptyState.classList.remove('hidden');
        showError(`Error loading report: ${error.message}`);
    }
}

function displayResults(latest, siteData) {
    emptyState.classList.add('hidden');
    reportLinksContainer.classList.remove('hidden');

    if (previousReportCard) {
        previousReportCard.classList.remove('hidden');
    }

    // Queue A
    const queueA = (latest.audit_summary.queue_a || []).slice(0, 10);
    const queueAList = document.getElementById('queueAList');
    if (queueA.length > 0) {
        queueAList.innerHTML = queueA.map(item => `
            <div class="queue-item ${item.status.toLowerCase()}">
                <div class="queue-item-path">${escapeHtml(item.path)}</div>
                <div class="queue-item-details">
                    <span class="queue-item-status ${item.status.toLowerCase()}">${item.status}</span>
                    <span>Score: ${(item.score * 100).toFixed(0)}%</span>
                    <span>${escapeHtml(item.note)}</span>
                </div>
            </div>
        `).join('');
        queueAContainer.classList.remove('hidden');
    } else {
        queueAList.innerHTML = '<p class="placeholder">No high-priority test-site fixes found.</p>';
        queueAContainer.classList.remove('hidden');
    }

    // Report links
    if (latest.links && latest.links.audit_html) {
        latestReportLink.href = latest.links.audit_html;
        latestReportLink.textContent = 'Open Latest Audit Report';
        latestReportLink.classList.remove('is-disabled');
        latestReportMeta.textContent = `Completed run: ${latest.display_date}`;
        latestReportCard.classList.remove('hidden');
    }

    if (siteData.previous && siteData.previous.links && siteData.previous.links.audit_html) {
        previousReportLink.href = siteData.previous.links.audit_html;
        previousReportLink.textContent = 'Open Previous Audit Report';
        previousReportLink.classList.remove('is-disabled');
        const improvements = siteData.previous.improvements || [];
        if (improvements.length > 0) {
            previousReportStats.innerHTML = improvements.map(item => `
                <div class="comparison-stat">
                    <span class="comparison-delta">+${item.delta}</span>
                    <span>${escapeHtml(item.label)}</span>
                </div>
            `).join('');
        } else {
            previousReportStats.innerHTML = '<p class="placeholder">No improvement trend available against the previous run.</p>';
        }
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
