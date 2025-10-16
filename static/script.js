const formatSelect = document.getElementById('format');
const qualitySelect = document.getElementById('quality');
const qualityHint = document.getElementById('qualityHint');
const statusDiv = document.getElementById('status');
const form = document.getElementById('downloadForm');
const submitBtn = document.getElementById('submitBtn');
const urlInput = document.getElementById('url');

const qualityOptions = {
    mp3: [
        { value: '128', label: '128 kbps', hint: 'Low quality' },
        { value: '192', label: '192 kbps (default)', hint: 'Standard quality' },
        { value: '256', label: '256 kbps', hint: 'High quality' },
        { value: '320', label: '320 kbps', hint: 'Best quality' }
    ],
    mp4: [
        { value: '360', label: '360p', hint: 'Low quality' },
        { value: '480', label: '480p', hint: 'Standard quality' },
        { value: '720', label: '720p (HD)', hint: 'High quality' },
        { value: '1080', label: '1080p (Full HD)', hint: 'Best quality' },
        { value: 'best', label: 'Best available', hint: 'Highest available' }
    ]
};

let currentPollInterval = null;
let isDownloading = false;


function updateQualityOptions() {
    const format = formatSelect.value;
    qualitySelect.innerHTML = "";
    
    qualityOptions[format].forEach(opt => {
        const option = document.createElement("option");
        option.value = opt.value;
        option.textContent = opt.label;
        
        // Set defaults
        if (format === 'mp3' && opt.value === '192') {
            option.selected = true;
        } else if (format === 'mp4' && opt.value === 'best') {
            option.selected = true;
        }
        
        qualitySelect.appendChild(option);
    });
    
    updateQualityHint();
}


function updateQualityHint() {
    const format = formatSelect.value;
    const quality = qualitySelect.value;
    const option = qualityOptions[format].find(o => o.value === quality);
    
    if (option) {
        qualityHint.textContent = option.hint;
    }
}


function renderStatus(task) {
    let statusClass = 'status-box';
    
    if (task.status === 'error') {
        statusClass += ' error';
    } else if (task.status === 'completed') {
        statusClass += ' success';
    } else if (task.failed_items > 0) {
        statusClass += ' warning';
    }
    
    const statusText = task.status.charAt(0).toUpperCase() + task.status.slice(1);
    let progressHtml = '';
    
    if (task.progress > 0 && task.progress < 100) {
        const progressPercent = task.progress.toFixed(1);
        progressHtml = `
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progressPercent}%"></div>
            </div>
            <div class="status-row">
                <span class="status-label">Progress:</span>
                <span class="status-value">${progressPercent}%</span>
            </div>
        `;
    }
    
    let speedEtaHtml = '';
    if (task.speed && task.eta) {
        const speedMB = (task.speed / (1024 * 1024)).toFixed(2);
        speedEtaHtml = `
            <div class="status-row">
                <span class="status-label">Speed:</span>
                <span class="status-value">${speedMB} MB/s</span>
            </div>
            <div class="status-row">
                <span class="status-label">ETA:</span>
                <span class="status-value">${formatSeconds(task.eta)}</span>
            </div>
        `;
    }
    
    let fileInfo = '';
    if (task.filename) {
        fileInfo = `
            <div class="status-row">
                <span class="status-label">File:</span>
                <span class="status-value">${escapeHtml(task.filename)}</span>
            </div>
        `;
    }
    
    let errorInfo = '';
    if (task.error) {
        errorInfo = `
            <div class="status-row">
                <span class="status-label error">Error:</span>
                <span class="status-value error">${escapeHtml(task.error)}</span>
            </div>
        `;
    }
    
    let failedInfo = '';
    if (task.failed_items > 0) {
        failedInfo = `
            <div class="status-row">
                <span class="status-label warning">Failed Items:</span>
                <span class="status-value warning">${task.failed_items}</span>
            </div>
        `;
    }
    
    statusDiv.innerHTML = `
        <div class="${statusClass}">
            <div class="status-row">
                <span class="status-label">Status:</span>
                <span class="status-value">${statusText}</span>
            </div>
            ${progressHtml}
            ${speedEtaHtml}
            ${fileInfo}
            ${failedInfo}
            ${errorInfo}
        </div>
    `;
}


function pollStatus(taskId) {
    if (currentPollInterval) {
        clearInterval(currentPollInterval);
    }
    
    currentPollInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/status/${taskId}`);
            
            if (!res.ok) {
                statusDiv.innerHTML = `
                    <div class="status-box error">
                        <div class="status-row">
                            <span class="status-label error">Error:</span>
                            <span class="status-value error">Failed to fetch status</span>
                        </div>
                    </div>
                `;
                clearInterval(currentPollInterval);
                isDownloading = false;
                submitBtn.disabled = false;
                return;
            }
            
            const task = await res.json();
            renderStatus(task);
            
            if (task.status === 'completed' || task.status === 'error') {
                clearInterval(currentPollInterval);
                isDownloading = false;
                submitBtn.disabled = false;
            }
        } catch (error) {
            console.error('Poll error:', error);
            statusDiv.innerHTML = `
                <div class="status-box error">
                    <div class="status-row">
                        <span class="status-label error">Error:</span>
                        <span class="status-value error">Connection lost</span>
                    </div>
                </div>
            `;
            clearInterval(currentPollInterval);
            isDownloading = false;
            submitBtn.disabled = false;
        }
    }, 2000);
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


form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (isDownloading) return;
    
    const url = urlInput.value.trim();
    const format = formatSelect.value;
    const quality = qualitySelect.value;
    const location = document.getElementById('location').value;
    
    if (!url) {
        statusDiv.innerHTML = `
            <div class="status-box error">
                <div class="status-row">
                    <span class="status-label error">Error:</span>
                    <span class="status-value error">URL cannot be empty</span>
                </div>
            </div>
        `;
        return;
    }
    
    isDownloading = true;
    submitBtn.disabled = true;
    statusDiv.innerHTML = `
        <div class="status-box">
            <div class="status-row">
                <span class="status-label">Status:</span>
                <span class="status-value">Starting download...</span>
            </div>
        </div>
    `;
    
    try {
        const res = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, format, quality, location })
        });
        
        const data = await res.json();
        
        if (!res.ok || !data.task_id) {
            statusDiv.innerHTML = `
                <div class="status-box error">
                    <div class="status-row">
                        <span class="status-label error">Error:</span>
                        <span class="status-value error">${escapeHtml(data.error || 'Failed to start download')}</span>
                    </div>
                </div>
            `;
            isDownloading = false;
            submitBtn.disabled = false;
            return;
        }
        
        pollStatus(data.task_id);
    
    } catch (error) {
        console.error('Submit error:', error);
        statusDiv.innerHTML = `
            <div class="status-box error">
                <div class="status-row">
                    <span class="status-label error">Error:</span>
                    <span class="status-value error">Network error. Please try again.</span>
                </div>
            </div>
        `;
        isDownloading = false;
        submitBtn.disabled = false;
    }
});

formatSelect.addEventListener('change', updateQualityOptions);

qualitySelect.addEventListener('change', updateQualityHint);

document.addEventListener('DOMContentLoaded', () => {
    updateQualityOptions();
});