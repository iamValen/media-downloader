const elements = {
    format: document.getElementById('format'),
    quality: document.getElementById('quality'),
    status: document.getElementById('status'),
    form: document.getElementById('downloadForm'),
    submitBtn: document.getElementById('submitBtn'),
    url: document.getElementById('url'),
    location: document.getElementById('location'),
    isAlbum: document.getElementById('isAlbum')
};

const QUALITY_OPTIONS = {
    mp3: [
        { value: '128', label: '128 kbps' },
        { value: '192', label: '192 kbps (default)' },
        { value: '256', label: '256 kbps' },
        { value: '320', label: '320 kbps' }
    ],
    mp4: [
        { value: '360', label: '360p' },
        { value: '480', label: '480p' },
        { value: '720', label: '720p (HD)' },
        { value: '1080', label: '1080p (Full HD)' },
        { value: 'best', label: 'Best available' }
    ]
};

const POLL_INTERVAL = 2000;
let currentPollInterval = null;
let isDownloading = false;
let locationPaths = {};

async function fetchConfig() {
    try {
        const res = await fetch('/api/config');
        if (res.ok) {
            const config = await res.json();
            locationPaths = {
                default: config.default_path,
                alt: config.alt_path
            };
            updateLocationOptions();
        }
    } catch (error) {
        console.error('Failed to fetch config:', error);
    }
}

function updateLocationOptions() {
    if (Object.keys(locationPaths).length === 0) return;

    const defaultLabel = locationPaths.default ? `Default (${locationPaths.default})` : 'Default';
    const altLabel = locationPaths.alt ? `Alternative (${locationPaths.alt})` : 'Alternative';

    elements.location.innerHTML = `
        <option value="default">${defaultLabel}</option>
        <option value="alt">${altLabel}</option>
    `;
}

function updateQualityOptions() {
    const format = elements.format.value;
    const options = QUALITY_OPTIONS[format];

    elements.quality.innerHTML = options.map(opt => {
        const isDefault = (format === 'mp3' && opt.value === '192') || 
                         (format === 'mp4' && opt.value === 'best');
        return `<option value="${opt.value}" ${isDefault ? 'selected' : ''}>${opt.label}</option>`;
    }).join('');
}

function renderStatus(task) {
    const statusClasses = ['status-box'];
    if (task.status === 'error') statusClasses.push('error');
    else if (task.status === 'completed') statusClasses.push('success');
    else if (task.failed_items > 0) statusClasses.push('warning');

    const statusText = task.status.charAt(0).toUpperCase() + task.status.slice(1);

    const sections = [
        createStatusRow('Status', statusText),
        createProgressBar(task),
        createSpeedEta(task),
        createFileInfo(task),
        createFailedInfo(task),
        createErrorInfo(task)
    ].filter(Boolean);

    elements.status.innerHTML = `<div class="${statusClasses.join(' ')}">
        ${sections.join('')}
    </div>`;
}

function createStatusRow(label, value, className = '') {
    return `<div class="status-row">
        <span class="status-label ${className}">${label}:</span>
        <span class="status-value ${className}">${escapeHtml(value)}</span>
    </div>`;
}

function createProgressBar(task) {
    if (task.progress <= 0 || task.progress >= 100) return null;
    const percent = task.progress.toFixed(1);
    return `<div class="progress-bar">
        <div class="progress-fill" style="width: ${percent}%"></div>
    </div>
    ${createStatusRow('Progress', `${percent}%`)}`;
}

function createSpeedEta(task) {
    if (!task.speed || !task.eta) return null;
    const speedMB = (task.speed / (1024 * 1024)).toFixed(2);
    return `${createStatusRow('Speed', `${speedMB} MB/s`)}
    ${createStatusRow('ETA', formatSeconds(task.eta))}`;
}

function createFileInfo(task) {
    return task.filename ? createStatusRow('File', task.filename) : null;
}

function createFailedInfo(task) {
    return task.failed_items > 0 
        ? createStatusRow('Failed Items', task.failed_items.toString(), 'warning') 
        : null;
}

function createErrorInfo(task) {
    return task.error ? createStatusRow('Error', task.error, 'error') : null;
}

function pollStatus(taskId) {
    stopPolling();
    currentPollInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/status/${taskId}`);
            if (!res.ok) {
                showError('Failed to fetch status');
                stopPolling();
                return;
            }
            const task = await res.json();
            renderStatus(task);
            if (task.status === 'completed' || task.status === 'error') {
                stopPolling();
            }
        } catch (error) {
            console.error('Poll error:', error);
            showError('Connection lost');
            stopPolling();
        }
    }, POLL_INTERVAL);
}

function stopPolling() {
    if (currentPollInterval) {
        clearInterval(currentPollInterval);
        currentPollInterval = null;
    }
    isDownloading = false;
    elements.submitBtn.disabled = false;
}

function showError(message) {
    elements.status.innerHTML = `<div class="status-box error">
        ${createStatusRow('Error', message, 'error')}
    </div>`;
}

function formatSeconds(seconds) {
    if (!seconds || seconds < 0) return 'Unknown';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

elements.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isDownloading) return;

    const url = elements.url.value.trim();
    if (!url) {
        showError('URL cannot be empty');
        return;
    }

    isDownloading = true;
    elements.submitBtn.disabled = true;
    elements.status.innerHTML = `<div class="status-box">
        ${createStatusRow('Status', 'Starting download...')}
    </div>`;

    try {
        const payload = {
            url,
            format: elements.format.value,
            quality: elements.quality.value,
            location: elements.location.value,
            isAlbum: elements.isAlbum.checked
        };

        const res = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok || !data.task_id) {
            showError(data.error || 'Failed to start download');
            isDownloading = false;
            elements.submitBtn.disabled = false;
            return;
        }

        pollStatus(data.task_id);
    } catch (error) {
        console.error('Submit error:', error);
        showError('Network error. Please try again.');
        isDownloading = false;
        elements.submitBtn.disabled = false;
    }
});

elements.format.addEventListener('change', updateQualityOptions);

document.addEventListener('DOMContentLoaded', () => {
    updateQualityOptions();
    fetchConfig();
});