/**
 * ============================================================================
 * DRDO PXE CHANDIPUR PORTAL - MAIN FRONTEND SCRIPT (main.js)
 * ============================================================================
 * Description: Manages live dashboard clock, telemetry sync, parameter slicers,
 * 15-minute auto-staging timer loop, and strict duplicate-protected form commits.
 * ============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
    // [INIT] Automatically set current live date and precise decimal hour on load
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const currentDateStr = `${year}-${month}-${day}`;
    const currentHourDecimal = now.getHours() + (now.getMinutes() / 60) + (now.getSeconds() / 3600);

    // Bind Parameter Slicer inputs
    const dateInput = document.getElementById('dateInput');
    if (dateInput) dateInput.value = currentDateStr;

    const hourInput = document.getElementById('hourInput');
    if (hourInput) hourInput.value = currentHourDecimal.toFixed(2);

    // Bind Staging Feed Form inputs
    const feedDate = document.getElementById('feedDate');
    if (feedDate) feedDate.value = currentDateStr;

    const feedTime = document.getElementById('feedTime');
    if (feedTime) {
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        feedTime.value = `${hh}:${mm}`;
    }

    // Initialize core portal modules
    initClock();
    initEventListeners();
    initAutoTelemetryLogger();
    fetchTelemetry();
});

let tideChartInstance = null;
let autoLogInterval = null;
let countdownInterval = null;
let totalSecondsLeft = 15 * 60; // 15 minutes = 900 seconds countdown window
let isSubmittingFlag = false;    // Strict frontend duplicate submission guard

/**
 * [MODULE 1] Digital Live Clock Display in Topbar
 */
function initClock() {
    setInterval(() => {
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0] + " IST";
        const clockEl = document.getElementById("digitalClock");
        if (clockEl) clockEl.innerText = timeStr;
    }, 1000);
}

/**
 * [MODULE 2] 15-Minute Auto-Staging Logger with Visual MM:SS Countdown
 */
function initAutoTelemetryLogger() {
    const toggle = document.getElementById("autoLogToggle");
    const timerSpan = document.getElementById("autoLogTimer");
    if (!toggle) return;

    toggle.addEventListener("change", function() {
        const resultDiv = document.getElementById("operatorCommitResult");
        
        if (this.checked) {
            if (resultDiv) {
                resultDiv.style.color = "#10b981";
                resultDiv.innerHTML = `<i class="fa-solid fa-sync fa-spin"></i> Auto-logging active (Syncing every 15 mins).`;
            }
            
            // Reset countdown and trigger immediately upon toggle activation
            totalSecondsLeft = 15 * 60;
            updateTimerDisplay(timerSpan);
            triggerAutoStagingCommit();

            // Set background interval for exactly 15 minutes (15 * 60 * 1000 ms)
            autoLogInterval = setInterval(() => {
                totalSecondsLeft = 15 * 60; // Reset countdown counter
                triggerAutoStagingCommit();
            }, 15 * 60 * 1000);

            // Set 1-second visual countdown ticker interval
            countdownInterval = setInterval(() => {
                if (totalSecondsLeft > 0) {
                    totalSecondsLeft--;
                }
                updateTimerDisplay(timerSpan);
            }, 1000);

        } else {
            // Stop and clear intervals when toggle is switched OFF
            if (autoLogInterval) clearInterval(autoLogInterval);
            if (countdownInterval) clearInterval(countdownInterval);
            
            totalSecondsLeft = 15 * 60;
            if (timerSpan) timerSpan.innerText = `15m 00s`;
            
            if (resultDiv) {
                resultDiv.style.color = "#94a3b8";
                resultDiv.innerText = "Auto-logging paused. Manual override enabled.";
            }
        }
    });
}

/**
 * Helper: Format remaining seconds into MM:SS format for UI timer span
 */
function updateTimerDisplay(timerSpan) {
    if (!timerSpan) return;
    const mins = Math.floor(totalSecondsLeft / 60);
    const secs = totalSecondsLeft % 60;
    timerSpan.innerText = `${mins}m ${String(secs).padStart(2, '0')}s`;
}

/**
 * [MODULE 3] Automated Staging Commit Dispatcher
 */
function triggerAutoStagingCommit() {
    const dateInput = document.getElementById('dateInput');
    const hourInput = document.getElementById('hourInput');
    const currentHour = hourInput ? parseFloat(hourInput.value) : 10;
    
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const currentDateStr = dateInput && dateInput.value ? dateInput.value : `${year}-${month}-${day}`;

    const payload = {
        date: currentDateStr,
        hour: currentHour,
        gauges_detail: {
            g_50m: parseFloat(document.getElementById("feedGauge50")?.value || 0.0),
            g_100m: parseFloat(document.getElementById("feedGauge100")?.value || 0.0),
            g_200m: parseFloat(document.getElementById("feedGauge200")?.value || 0.0),
            g_500m: parseFloat(document.getElementById("feedGauge500")?.value || 0.0),
            g_1000m: parseFloat(document.getElementById("feedGauge1000")?.value || 2.5)
        },
        is_safe: 1
    };

    fetch('/save_staging', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        const resultDiv = document.getElementById("operatorCommitResult");
        if(data.status === 'success' && resultDiv && document.getElementById("autoLogToggle")?.checked) {
            resultDiv.style.color = "#10b981";
            resultDiv.innerHTML = `<i class="fa-solid fa-check-circle"></i> Auto-committed! Hash: <code>${data.commit_hash}</code>`;
        }
    })
    .catch(err => console.error('Auto-Staging Error:', err));
}

/**
 * [MODULE 4] Event Listeners & Strict Duplicate-Protected Manual Form Submission
 */
function initEventListeners() {
    const inputs = ['dateInput', 'hourInput'];
    
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => {
                updateLabels();
                fetchTelemetry();
            });
            el.addEventListener('change', () => {
                updateLabels();
                fetchTelemetry();
            });
        }
    });

    const btnUpdate = document.getElementById("btnUpdate");
    if (btnUpdate) {
        btnUpdate.addEventListener("click", (e) => {
            e.preventDefault();
            fetchTelemetry();
        });
    }

    // Operator Feed In-line Form Submission Handler with Strict Duplicate Protection
    const operatorForm = document.getElementById("comprehensiveFeedForm");
    if (operatorForm) {
        if (operatorForm.dataset.bound === "true") return;
        operatorForm.dataset.bound = "true";

        operatorForm.addEventListener("submit", function(e) {
            e.preventDefault();
            
            // Strict defense: Prevent concurrent/double submissions
            if (isSubmittingFlag) return;
            isSubmittingFlag = true;

            const submitBtn = operatorForm.querySelector("button[type='submit']");
            if (submitBtn) submitBtn.disabled = true;

            const resultDiv = document.getElementById("operatorCommitResult");
            const timeStr = document.getElementById("feedTime").value;
            const [hrs, mins] = timeStr.split(':').map(Number);
            const decimalHour = hrs + (mins / 60);
            
            const payload = {
                date: document.getElementById("feedDate").value,
                hour: decimalHour,
                gauges_detail: {
                    g_50m: parseFloat(document.getElementById("feedGauge50").value),
                    g_100m: parseFloat(document.getElementById("feedGauge100").value),
                    g_200m: parseFloat(document.getElementById("feedGauge200").value),
                    g_500m: parseFloat(document.getElementById("feedGauge500").value),
                    g_1000m: parseFloat(document.getElementById("feedGauge1000").value)
                },
                is_safe: 1
            };

            fetch('/save_staging', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                isSubmittingFlag = false; // Reset submission flag
                if (submitBtn) submitBtn.disabled = false;

                if(data.status === 'success') {
                    if (resultDiv) {
                        resultDiv.style.color = "#10b981";
                        resultDiv.innerHTML = `<i class="fa-solid fa-check-circle"></i> Committed! Hash: <code>${data.commit_hash}</code>`;
                    }
                } else {
                    if (resultDiv) {
                        resultDiv.style.color = "#ef4444";
                        resultDiv.innerText = "Failed to push into Staging DB.";
                    }
                }
            })
            .catch(err => {
                isSubmittingFlag = false;
                if (submitBtn) submitBtn.disabled = false;
                console.error('Submission Error:', err);
            });
        });
    }
}

/**
 * [MODULE 5] Parameter Slicer Label & Time Conversion Utility
 */
function updateLabels() {
    const hourInputEl = document.getElementById('hourInput');
    if (!hourInputEl) return;
    const hourDecimal = parseFloat(hourInputEl.value);
    const hrs = Math.floor(hourDecimal);
    const mins = Math.round((hourDecimal - hrs) * 60);
    const timeStr = `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')} IST`;
    
    const hourValEl = document.getElementById('hourVal');
    if (hourValEl) hourValEl.innerText = timeStr;
}

/**
 * [MODULE 6] Backend Telemetry Fetch & Prediction Sync
 */
function fetchTelemetry() {
    updateLabels();
    
    const hourInputEl = document.getElementById('hourInput');
    const dateInputEl = document.getElementById('dateInput');
    const currentHour = hourInputEl ? parseFloat(hourInputEl.value) : 10;
    
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const defaultDate = `${year}-${month}-${day}`;

    const payload = {
        date: dateInputEl && dateInputEl.value ? dateInputEl.value : defaultDate,
        hour: currentHour
    };

    fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            updateDashboardUI(data.prediction, currentHour);
        }
    })
    .catch(err => console.error("Telemetry Sync Error:", err));
}

/**
 * [MODULE 7] Dashboard UI Rendering & KPI Updates
 */
function updateDashboardUI(p, activeHour) {
    const banner = document.getElementById("clearanceBanner");
    const statusIcon = document.getElementById("statusIcon");
    const statusTitle = document.getElementById("statusTitle");
    const tideStageBadge = document.getElementById("tideStageBadge");
    const statusDesc = document.getElementById("statusDesc");
    const authCode = document.getElementById("authCode");

    if (p.range_state === "CLEAR") {
        banner.className = "mission-status-banner banner-safe";
        if(statusIcon) statusIcon.className = "fa-solid fa-circle-check text-success";
        if(authCode) authCode.innerText = "PXE-AUTH-CLEAR";
    } else if (p.range_state === "WARNING") {
        banner.className = "mission-status-banner banner-warning";
        if(statusIcon) statusIcon.className = "fa-solid fa-triangle-exclamation text-warning";
        if(authCode) authCode.innerText = "PXE-AUTH-HOLD";
    } else {
        banner.className = "mission-status-banner banner-unsafe";
        if(statusIcon) statusIcon.className = "fa-solid fa-triangle-exclamation text-danger";
        if(authCode) authCode.innerText = "PXE-AUTH-HOLD";
    }

    if (statusTitle && p.banner_title) {
        statusTitle.innerText = p.banner_title;
    }
    if (statusDesc && p.banner_desc) {
        statusDesc.innerText = p.banner_desc;
    }

    if(tideStageBadge) {
        tideStageBadge.innerText = p.tide_stage;
        tideStageBadge.className = `pbi-badge-pill ${p.tide_badge}`;
    }

    const kpiLevel = document.getElementById("kpiLevel");
    if(kpiLevel) kpiLevel.innerHTML = `${p.gauge_level_m} <small>m</small>`;
    
    const kpiExposure = document.getElementById("kpiExposure");
    if(kpiExposure) kpiExposure.innerHTML = `${Number(p.exposure_m).toFixed(2)} <small>m</small>`;
    
    const kpi500m = document.getElementById("kpi500m");
    if(kpi500m) kpi500m.innerHTML = `${p.stumps.find(s => s.distance === 500)?.water_depth.toFixed(2) || '0.00'} <small>m</small>`;
    
    const kpiRate = document.getElementById("kpiRate");
    if(kpiRate) kpiRate.innerHTML = `${p.rate_of_change_m_hr} <small>m/h</small>`;
    
    const kpiTemp = document.getElementById("kpiTemp");
    if(kpiTemp) kpiTemp.innerHTML = `${p.weather.temperature_c} <small>&deg;C</small>`;
    
    const kpiWeatherSummary = document.getElementById("kpiWeatherSummary");
    if(kpiWeatherSummary) kpiWeatherSummary.innerText = p.weather.weather_desc;

    const wTemp = document.getElementById("wTemp");
    if(wTemp) wTemp.innerHTML = `${p.weather.temperature_c} &deg;C`;
    const wHumidity = document.getElementById("wHumidity");
    if(wHumidity) wHumidity.innerText = `${p.weather.humidity_pct} %`;
    const wPressure = document.getElementById("wPressure");
    if(wPressure) wPressure.innerText = `${p.weather.pressure_hpa} hPa`;
    const wVisibility = document.getElementById("wVisibility");
    if(wVisibility) wVisibility.innerText = `${p.weather.visibility_km} km`;
    const wVector = document.getElementById("wVector");
    if(wVector) wVector.innerHTML = `${p.weather.wind_speed_ms} m/s &bull; ${p.weather.wind_dir_deg}&deg;`;

    // Spatial Stumps Cards Render
    const stumpGrid = document.getElementById("stumpGrid");
    if (stumpGrid) {
        stumpGrid.innerHTML = "";
        p.stumps.forEach(s => {
            const card = document.createElement("div");
            card.className = `stump-card-item ${s.is_dry ? 'is-dry' : 'is-flooded'}`;
            card.innerHTML = `
                <div class="stump-distance-title">${s.distance}m Mark</div>
                <div class="stump-depth-display">${s.water_depth.toFixed(2)}m</div>
                <span class="stump-status-tag">${s.status}</span>
            `;
            stumpGrid.appendChild(card);
        });
    }

    // RSO Audit Checklist Render
    const checklistContainer = document.getElementById("checklistContainer");
    if (checklistContainer) {
        checklistContainer.innerHTML = "";
        p.reasons.forEach(r => {
            const item = document.createElement("div");
            item.className = "check-item";
            item.style.borderLeft = `4px solid ${r.pass ? 'var(--pbi-safe)' : 'var(--pbi-danger)'}`;
            item.innerHTML = `
                <i class="fa-solid ${r.pass ? 'fa-check' : 'fa-xmark'}"></i>
                <span>${r.text}</span>
            `;
            checklistContainer.appendChild(item);
        });
    }

    // Coastal Environment Simulation (Mahaul) Render
    if (p.mahaul) {
        const mahaulPhoto = document.getElementById("mahaulPhoto");
        const photoTag = document.getElementById("photoTag");
        const photoDist = document.getElementById("photoDist");
        const photoTitle = document.getElementById("photoTitle");
        const photoDesc = document.getElementById("photoDesc");
        
        if(mahaulPhoto) mahaulPhoto.src = p.mahaul.img;
        if(photoTag) photoTag.innerText = p.mahaul.tag;
        if(photoDist) photoDist.innerText = p.mahaul.dist;
        if(photoTitle) photoTitle.innerText = p.mahaul.title;
        if(photoDesc) photoDesc.innerText = p.mahaul.desc;
    }

    updateChart(p.forecast_24h, activeHour);
}

/**
 * [MODULE 8] Chart.js Tidal Horizon Rendering & Crosshair Plugin
 */
function updateChart(forecastData, activeHour) {
    const ctx = document.getElementById('tideForecastChart');
    if (!ctx) return;

    const labels = forecastData.map(d => d.label);
    const waterLevels = forecastData.map(d => d.water_level);

    const pointRadii = labels.map((_, index) => (Math.abs(index - activeHour) < 0.5 ? 7 : 2));
    const pointColors = labels.map((_, index) => (Math.abs(index - activeHour) < 0.5 ? '#ffaa00' : '#00ffcc'));

    const crosshairPlugin = {
        id: 'crosshairPlugin',
        afterDraw: (chart) => {
            const currentHour = chart.config.options.activeHour;
            if (currentHour === undefined || currentHour === null) return;
            const meta = chart.getDatasetMeta(0);
            if (!meta.data || meta.data.length === 0) return;
            
            const index = Math.min(Math.max(Math.round(currentHour), 0), meta.data.length - 1);
            const point = meta.data[index];
            if (!point) return;
            
            const x = point.x;
            const y = point.y;

            const topY = chart.scales.y.top;
            const bottomY = chart.scales.y.bottom;
            const leftX = chart.scales.x.left;
            const rightX = chart.scales.x.right;

            const ctx = chart.ctx;
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x, topY);
            ctx.lineTo(x, bottomY);
            ctx.moveTo(leftX, y);
            ctx.lineTo(rightX, y);
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = '#ffaa00';
            ctx.setLineDash([4, 4]);
            ctx.stroke();
            ctx.restore();
        }
    };

    if (tideChartInstance) {
        tideChartInstance.config.options.activeHour = activeHour;
        tideChartInstance.data.labels = labels;
        tideChartInstance.data.datasets[0].data = waterLevels;
        tideChartInstance.data.datasets[0].pointRadius = pointRadii;
        tideChartInstance.data.datasets[0].pointBackgroundColor = pointColors;
        tideChartInstance.update();
    } else {
        tideChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Predicted Tide Level (m)',
                    data: waterLevels,
                    borderColor: '#00ffcc',
                    backgroundColor: 'rgba(0, 255, 204, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: pointRadii,
                    pointBackgroundColor: pointColors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                activeHour: activeHour,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } }
                }
            },
            plugins: [crosshairPlugin]
        });
    }
}