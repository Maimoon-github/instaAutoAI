/**
 * AI Pipeline Dashboard - WebSocket & UI Controller
 * Connects only when a job is selected.
 */

(function() {
  'use strict';

  // Configuration from Django template
  const CONFIG = window.CONFIG || {
    websocketUrl: '',  // no default connection
    userId: 'anonymous',
    csrfToken: ''
  };

  // State
  let ws = null;
  let currentJobId = null;
  let heartbeatTimer = null;
  const HEARTBEAT_INTERVAL = 30000;

  // DOM Elements (same as before)
  const elements = {
    statusIndicator: document.getElementById('statusIndicator'),
    statusText: document.getElementById('statusText'),
    jobList: document.getElementById('jobList'),
    toastContainer: document.getElementById('toastContainer'),
    pendingCount: document.getElementById('pendingCount'),
    runningCount: document.getElementById('runningCount'),
    completedCount: document.getElementById('completedCount'),
    failedCount: document.getElementById('failedCount'),
    vram0Bar: document.getElementById('vram0Bar'),
    vram0Text: document.getElementById('vram0Text'),
    refreshBtn: document.getElementById('refreshBtn'),
    closePanel: document.getElementById('closePanel'),
    jobDetails: document.getElementById('jobDetails'),
    detailsContent: document.getElementById('detailsContent'),
    detailsActions: document.getElementById('detailsActions')
  };

  // Helper: Update connection status display
  function updateConnectionStatus(status, text) {
    if (!elements.statusIndicator || !elements.statusText) return;
    elements.statusIndicator.className = 'status-indicator ' + status;
    elements.statusText.textContent = text;
  }

  // WebSocket event handlers
  function handleOpen() {
    console.log('WebSocket connected for job', currentJobId);
    updateConnectionStatus('connected', 'Live');
    startHeartbeat();
    // Optionally send subscribe message (consumer may ignore)
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'subscribe', user_id: CONFIG.userId }));
    }
  }

  function handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      processMessage(data);
    } catch (error) {
      console.error('Failed to parse message:', error);
      showToast('Failed to process server message', 'error');
    }
  }

  function handleClose(event) {
    console.log('WebSocket closed for job', currentJobId, event.code, event.reason);
    stopHeartbeat();
    updateConnectionStatus('disconnected', 'Disconnected');
    ws = null;
    currentJobId = null;
  }

  function handleError(error) {
    console.error('WebSocket error:', error);
    updateConnectionStatus('error', 'Connection Error');
  }

  // Message processing (unchanged)
  function processMessage(data) {
    switch (data.type) {
      case 'job_update':
        updateJob(data.job);
        break;
      case 'job_created':
        addJob(data.job);
        showToast(`Job ${data.job.id} created`, 'success');
        break;
      case 'job_completed':
        updateJob(data.job);
        showToast(`Job ${data.job.id} completed`, 'success');
        break;
      case 'job_failed':
        updateJob(data.job);
        showToast(`Job ${data.job.id} failed`, 'error');
        break;
      case 'stats_update':
        updateStats(data.stats);
        break;
      case 'vram_update':
        updateVRAM(data.vram);
        break;
      case 'pong':
        // Heartbeat response
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  }

  function sendMessage(data) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, message dropped');
    }
  }

  function startHeartbeat() {
    if (heartbeatTimer) clearInterval(heartbeatTimer);
    heartbeatTimer = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'ping' });
      }
    }, HEARTBEAT_INTERVAL);
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  }

  // UI updates (unchanged)
  function updateStats(stats) {
    if (elements.pendingCount) elements.pendingCount.textContent = stats.pending || 0;
    if (elements.runningCount) elements.runningCount.textContent = stats.running || 0;
    if (elements.completedCount) elements.completedCount.textContent = stats.completed || 0;
    if (elements.failedCount) elements.failedCount.textContent = stats.failed || 0;
  }

  function updateVRAM(vram) {
    if (!elements.vram0Bar || !elements.vram0Text) return;
    const gpu = vram[0];
    if (!gpu) return;
    const percent = (gpu.used / gpu.total) * 100;
    elements.vram0Bar.style.width = percent + '%';
    elements.vram0Bar.setAttribute('aria-valuenow', percent);
    elements.vram0Text.textContent = `${gpu.used.toFixed(1)} / ${gpu.total.toFixed(1)} GB`;
  }

  function addJob(job) {
    if (!elements.jobList) return;
    const jobEl = createJobElement(job);
    elements.jobList.insertBefore(jobEl, elements.jobList.firstChild);
    const skeleton = elements.jobList.querySelector('.skeleton');
    if (skeleton) skeleton.remove();
  }

  function updateJob(job) {
    if (!elements.jobList) return;
    const existing = document.querySelector(`[data-job-id="${job.id}"]`);
    if (existing) {
      existing.outerHTML = createJobElement(job).outerHTML;
    } else {
      addJob(job);
    }
  }

  function createJobElement(job) {
    const div = document.createElement('article');
    div.className = 'job-item';
    div.setAttribute('role', 'listitem');
    div.setAttribute('data-job-id', job.id);
    div.innerHTML = `
      <div class="job-status-indicator ${job.status}"></div>
      <div class="job-info">
        <div class="job-title">${escapeHtml(job.name || `Job ${job.id}`)}</div>
        <div class="job-meta">${job.type} • ${formatTime(job.created_at)}</div>
      </div>
    `;
    div.addEventListener('click', () => loadJobDetails(job.id));
    return div;
  }

  // Main entry point for job selection
  function loadJobDetails(jobId) {
    // Connect to WebSocket for this job
    connectToJob(jobId);
    // Fetch job details via AJAX
    fetch(`/jobs/${jobId}/detail/`, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': CONFIG.csrfToken
      }
    })
    .then(response => {
      if (!response.ok) throw new Error('Failed to load');
      return response.text();
    })
    .then(html => {
      if (elements.detailsContent) elements.detailsContent.innerHTML = html;
      if (elements.detailsActions) elements.detailsActions.hidden = false;
      const panel = document.querySelector('.dashboard-panel');
      if (panel && window.innerWidth <= 1024) panel.classList.add('active');
    })
    .catch(error => {
      console.error('Failed to load job details:', error);
      showToast('Failed to load job details', 'error');
    });
  }

  // WebSocket connection for a specific job
  function connectToJob(jobId) {
    if (ws) {
      ws.close();
      ws = null;
    }
    currentJobId = jobId;
    const wsUrl = `ws://${window.location.host}/ws/jobs/${jobId}/`;
    ws = new WebSocket(wsUrl);
    ws.onopen = handleOpen;
    ws.onmessage = handleMessage;
    ws.onclose = handleClose;
    ws.onerror = handleError;
  }

  // Utility functions
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function formatTime(timestamp) {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = (now - date) / 1000;
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  }

  function showToast(message, type = 'info') {
    if (!elements.toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'alert');
    elements.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }

  // Event listeners for UI elements
  function initEventListeners() {
    if (elements.refreshBtn) {
      elements.refreshBtn.addEventListener('click', () => {
        elements.refreshBtn.classList.add('spinning');
        // You can send a refresh request over WebSocket if connected
        sendMessage({ type: 'refresh_jobs' });
        setTimeout(() => elements.refreshBtn?.classList.remove('spinning'), 1000);
      });
    }
    if (elements.closePanel) {
      elements.closePanel.addEventListener('click', () => {
        const panel = document.querySelector('.dashboard-panel');
        if (panel) panel.classList.remove('active');
      });
    }
    document.querySelectorAll('.sidebar-link').forEach(link => {
      link.addEventListener('click', (e) => {
        document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
        e.target.classList.add('active');
      });
    });
    // HTMX fallback
    document.addEventListener('click', (e) => {
      const target = e.target.closest('[data-hx-get]');
      if (!target || typeof htmx !== 'undefined') return;
      e.preventDefault();
      const url = target.getAttribute('data-hx-get');
      const targetId = target.getAttribute('data-hx-target');
      fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.text())
        .then(html => {
          const dest = document.querySelector(targetId);
          if (dest) dest.innerHTML = html;
        });
    });
  }

  // Initialisation
  function init() {
    initEventListeners();
    // Log render time
    if (window.performance) {
      const timing = window.performance.timing;
      const loadTime = timing.loadEventEnd - timing.navigationStart;
      const renderTime = document.getElementById('render-time');
      if (renderTime) renderTime.textContent = `Rendered in ${loadTime}ms`;
    }
    // No automatic WebSocket connection
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Debug API
  window.PipelineDashboard = {
    connectToJob,
    send: sendMessage,
    status: () => ws?.readyState,
    currentJob: () => currentJobId
  };
})();