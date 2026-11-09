/**
 * EnerSense – Smart Energy Intelligence Platform
 * Main Frontend Script  |  v2.0
 *
 * Sections:
 *   1. Theme Toggle
 *   2. Sidebar Mobile Toggle
 *   3. Flash Auto-Dismiss
 *   4. Form Validation (Prediction)
 *   5. Loading Overlay
 *   6. Live Prediction Preview
 *   7. Toast Notification
 *   8. Energy Score Animation
 *   9. Chart Helpers (getChartColors, chartDefaults)
 *  10. Number Counter Animation
 *  11. Appliance Preset Selector
 *  12. Advisor AJAX Chat
 *  13. Range Slider Sync
 *  14. Table Row Click Navigation
 */

document.addEventListener('DOMContentLoaded', function () {

    /* ================================================================
       1. THEME TOGGLE
       ================================================================ */
    const THEME_KEY = 'enersense-theme';
    const html = document.documentElement;

    /**
     * Apply a theme ('light' | 'dark') to the document and persist it.
     */
    function applyTheme(theme) {
        html.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);
        updateThemeUI(theme);

        // Notify charts to re-render with new color palette
        if (typeof window.renderCharts === 'function') {
            setTimeout(window.renderCharts, 50);
        }
    }

    /**
     * Update all theme-toggle button icons and labels.
     */
    function updateThemeUI(theme) {
        const isDark = theme === 'dark';
        const toggleBtns = document.querySelectorAll('#themeToggle, #mobileThemeToggle, .theme-toggle-btn');

        toggleBtns.forEach(function (btn) {
            const icon  = btn.querySelector('i');
            const label = btn.querySelector('.theme-label');

            if (icon) {
                icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
            }
            if (label) {
                label.textContent = isDark ? 'Light Mode' : 'Dark Mode';
            }
            btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
            btn.setAttribute('title',      isDark ? 'Switch to light mode' : 'Switch to dark mode');
        });
    }

    function toggleTheme() {
        const current = html.getAttribute('data-theme') || 'light';
        applyTheme(current === 'dark' ? 'light' : 'dark');
    }

    // Load saved preference (default = light)
    const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
    applyTheme(savedTheme);

    // Wire up toggle buttons
    document.querySelectorAll('#themeToggle, #mobileThemeToggle, .theme-toggle-btn').forEach(function (btn) {
        btn.addEventListener('click', toggleTheme);
    });


    /* ================================================================
       2. SIDEBAR MOBILE TOGGLE
       ================================================================ */
    const sidebar        = document.querySelector('.sidebar');
    const overlay        = document.getElementById('sidebarOverlay');
    const toggleBtn      = document.getElementById('mobileSidebarToggle');

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('open');
        if (overlay) overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            sidebar && sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
        });
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Close sidebar on nav-item click when in mobile width
    document.querySelectorAll('.sidebar .nav-item').forEach(function (item) {
        item.addEventListener('click', function () {
            if (window.innerWidth < 1024) {
                closeSidebar();
            }
        });
    });

    // Close sidebar on window resize if it becomes desktop
    window.addEventListener('resize', function () {
        if (window.innerWidth >= 1024) {
            closeSidebar();
        }
    });


    /* ================================================================
       3. FLASH AUTO-DISMISS
       ================================================================ */
    function dismissAlert(alertEl) {
        alertEl.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(function () {
            alertEl.remove();
        }, 320);
    }

    // Wire close buttons
    document.querySelectorAll('.alert-close-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const alert = btn.closest('.alert-custom');
            if (alert) dismissAlert(alert);
        });
    });

    // Auto-dismiss after 5 seconds
    document.querySelectorAll('.alert-custom').forEach(function (alert) {
        const delay = parseInt(alert.getAttribute('data-delay') || '5000', 10);
        setTimeout(function () {
            if (alert.isConnected) dismissAlert(alert);
        }, delay);
    });


    /* ================================================================
       4. FORM VALIDATION (Prediction Form)
       ================================================================ */
    const predictionForm = document.getElementById('predictionForm');

    if (predictionForm) {
        const rules = {
            voltage:               { min: 150,  max: 300, label: 'Voltage',               integer: false },
            current:               { min: 0.1,  max: 50,  label: 'Current',               integer: false },
            usage_hours:           { min: 0.1,  max: 24,  label: 'Usage Hours',           integer: false },
            number_of_appliances:  { min: 1,    max: 50,  label: 'Number of Appliances',  integer: true  },
            temperature:           { min: -10,  max: 60,  label: 'Temperature',           integer: false },
            previous_consumption:  { min: 0,    max: 200, label: 'Previous Consumption',  integer: false },
        };

        predictionForm.addEventListener('submit', function (e) {
            let firstError = null;

            // Clear previous errors
            predictionForm.querySelectorAll('.is-invalid').forEach(function (el) {
                el.classList.remove('is-invalid');
            });
            predictionForm.querySelectorAll('.invalid-feedback').forEach(function (el) {
                el.remove();
            });

            for (const [fieldName, rule] of Object.entries(rules)) {
                const input = predictionForm.querySelector('[name="' + fieldName + '"]');
                if (!input) continue;

                const rawVal = input.value.trim();
                const val    = parseFloat(rawVal);

                if (rawVal === '' || isNaN(val)) {
                    markInvalid(input, rule.label + ' is required.');
                    if (!firstError) firstError = input;
                    continue;
                }

                if (rule.integer && !Number.isInteger(val)) {
                    markInvalid(input, rule.label + ' must be a whole number.');
                    if (!firstError) firstError = input;
                    continue;
                }

                if (val < rule.min || val > rule.max) {
                    markInvalid(input, rule.label + ' must be between ' + rule.min + ' and ' + rule.max + '.');
                    if (!firstError) firstError = input;
                }
            }

            if (firstError) {
                e.preventDefault();
                firstError.focus();
                window.showToast('Please fix the highlighted errors before submitting.', 'danger');
            }
        });

        function markInvalid(input, message) {
            input.classList.add('is-invalid');
            const fb = document.createElement('div');
            fb.className = 'invalid-feedback';
            fb.textContent = message;
            input.parentNode.insertBefore(fb, input.nextSibling);
        }
    }


    /* ================================================================
       5. LOADING OVERLAY
       ================================================================ */
    const loadingOverlay = document.querySelector('.loading-overlay');

    function showLoading() {
        if (loadingOverlay) loadingOverlay.classList.add('active');
    }
    function hideLoading() {
        if (loadingOverlay) loadingOverlay.classList.remove('active');
    }

    // Show on prediction form submit (if no validation errors)
    if (predictionForm) {
        predictionForm.addEventListener('submit', function () {
            // Only show if form has no invalid fields
            if (!predictionForm.querySelector('.is-invalid')) {
                showLoading();
            }
        });
    }

    // Show on any form with data-loading="true"
    document.querySelectorAll('form[data-loading="true"]').forEach(function (form) {
        form.addEventListener('submit', function () {
            showLoading();
        });
    });

    // Hide on page show (back-forward cache)
    window.addEventListener('pageshow', function (e) {
        if (e.persisted) hideLoading();
    });

    // Expose globally
    window.showLoading = showLoading;
    window.hideLoading = hideLoading;


    /* ================================================================
       6. LIVE PREDICTION PREVIEW
       ================================================================ */
    const voltageInput    = document.getElementById('voltage');
    const currentInput    = document.getElementById('current');
    const usageHrsInput   = document.getElementById('usage_hours');
    const physicsPreview  = document.getElementById('physicsPreview');
    const physicsValue    = document.getElementById('physicsValue');

    function updatePhysicsPreview() {
        if (!physicsPreview || !physicsValue) return;

        const v = parseFloat(voltageInput   ? voltageInput.value   : 0) || 0;
        const i = parseFloat(currentInput   ? currentInput.value   : 0) || 0;
        const t = parseFloat(usageHrsInput  ? usageHrsInput.value  : 0) || 0;

        if (v > 0 && i > 0 && t > 0) {
            const powerKW  = (v * i) / 1000;            // kW
            const energyKWh = powerKW * t;               // kWh
            physicsValue.textContent = energyKWh.toFixed(3);
            physicsPreview.classList.add('visible');
        } else {
            physicsPreview.classList.remove('visible');
        }
    }

    [voltageInput, currentInput, usageHrsInput].forEach(function (el) {
        if (el) {
            el.addEventListener('input', updatePhysicsPreview);
            el.addEventListener('change', updatePhysicsPreview);
        }
    });

    // Initial call in case values are pre-filled
    updatePhysicsPreview();


    /* ================================================================
       7. TOAST NOTIFICATION
       ================================================================ */

    /**
     * Show a toast notification.
     * @param {string} message
     * @param {string} type - 'success' | 'danger' | 'warning' | 'info'
     * @param {number} [duration=4000]
     */
    window.showToast = function (message, type, duration) {
        type = type || 'info';
        duration = duration || 4000;

        let container = document.querySelector('.flash-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'flash-container';
            document.body.appendChild(container);
        }

        const iconMap = {
            success: 'fa-check-circle',
            danger:  'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info:    'fa-info-circle',
        };

        const toast = document.createElement('div');
        toast.className = 'alert-custom alert-' + type;
        toast.innerHTML =
            '<i class="fas ' + (iconMap[type] || 'fa-info-circle') + ' alert-icon"></i>' +
            '<span class="alert-text">' + escapeHtml(message) + '</span>' +
            '<button class="alert-close-btn" aria-label="Close"><i class="fas fa-times"></i></button>';

        container.appendChild(toast);

        // Wire close button
        toast.querySelector('.alert-close-btn').addEventListener('click', function () {
            dismissAlert(toast);
        });

        // Auto-dismiss
        setTimeout(function () {
            if (toast.isConnected) dismissAlert(toast);
        }, duration);
    };

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }


    /* ================================================================
       8. ENERGY SCORE ANIMATION
       ================================================================ */

    /**
     * Animate an SVG score ring.
     * The ring element should have class .score-ring-fill and data-score (0-100).
     */
    function animateScoreRings() {
        document.querySelectorAll('.score-ring-fill').forEach(function (ring) {
            const score = parseFloat(ring.getAttribute('data-score') || '0');
            const r     = parseFloat(ring.getAttribute('r') || '56');
            const circumference = 2 * Math.PI * r;

            ring.style.strokeDasharray  = circumference;
            ring.style.strokeDashoffset = circumference; // start fully hidden

            // Trigger animation after short paint delay
            requestAnimationFrame(function () {
                requestAnimationFrame(function () {
                    const offset = circumference - (score / 100) * circumference;
                    ring.style.strokeDashoffset = offset;
                });
            });
        });
    }

    animateScoreRings();


    /* ================================================================
       9. CHART HELPERS
       ================================================================ */

    /**
     * Returns theme-aware color palette for Chart.js.
     */
    window.getChartColors = function () {
        const isDark = html.getAttribute('data-theme') === 'dark';
        return {
            text:         isDark ? '#94a3b8' : '#475569',
            grid:         isDark ? 'rgba(148,163,184,0.08)' : 'rgba(0,0,0,0.05)',
            bg:           isDark ? '#1e293b' : '#ffffff',
            accent:       '#10b981',
            accentAlpha:  'rgba(16,185,129,0.15)',
            blue:         '#6366f1',
            blueAlpha:    'rgba(99,102,241,0.15)',
            warning:      '#f59e0b',
            warningAlpha: 'rgba(245,158,11,0.15)',
            danger:       '#ef4444',
            dangerAlpha:  'rgba(239,68,68,0.15)',
            purple:       '#8b5cf6',
            purpleAlpha:  'rgba(139,92,246,0.15)',
        };
    };

    /**
     * Returns default Chart.js options object, themed to current mode.
     */
    window.chartDefaults = function () {
        const c = window.getChartColors();
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 700,
                easing: 'easeInOutQuart',
            },
            plugins: {
                legend: {
                    labels: {
                        color:    c.text,
                        font:     { family: 'Inter', size: 11 },
                        padding:  12,
                        boxWidth: 12,
                        boxHeight: 12,
                    },
                },
                tooltip: {
                    backgroundColor: c.bg,
                    titleColor:      c.text,
                    bodyColor:       c.text,
                    borderColor:     c.grid,
                    borderWidth:     1,
                    padding:         10,
                    cornerRadius:    8,
                    displayColors:   true,
                    boxPadding:      4,
                },
            },
            scales: {
                x: {
                    ticks: { color: c.text, font: { family: 'Inter', size: 10 } },
                    grid:  { color: c.grid },
                    border: { color: c.grid },
                },
                y: {
                    ticks: { color: c.text, font: { family: 'Inter', size: 10 } },
                    grid:  { color: c.grid },
                    border: { color: c.grid },
                },
            },
        };
    };

    // Re-render charts on theme change (pages hook into window.renderCharts)
    window.renderCharts = null; // pages override this


    /* ================================================================
       10. NUMBER COUNTER ANIMATION
       ================================================================ */

    /**
     * Animate a number from 0 to its data-counter value.
     * Attributes:
     *   data-counter  – target number (float)
     *   data-decimals – decimal places (default 0)
     *   data-prefix   – text before number (e.g. '$')
     *   data-suffix   – text after number (e.g. '%')
     */
    function animateCounter(el) {
        const target   = parseFloat(el.getAttribute('data-counter') || '0');
        const decimals = parseInt(el.getAttribute('data-decimals')  || '0', 10);
        const prefix   = el.getAttribute('data-prefix') || '';
        const suffix   = el.getAttribute('data-suffix') || '';
        const duration = 1200;

        let startTime = null;

        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            const elapsed  = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Cubic ease-out
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = eased * target;

            el.textContent = prefix + value.toFixed(decimals) + suffix;

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                el.textContent = prefix + target.toFixed(decimals) + suffix;
            }
        }

        requestAnimationFrame(step);
    }

    // Use IntersectionObserver so counters start when visible
    if ('IntersectionObserver' in window) {
        const counterObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.4 });

        document.querySelectorAll('[data-counter]').forEach(function (el) {
            counterObserver.observe(el);
        });
    } else {
        // Fallback: run immediately
        document.querySelectorAll('[data-counter]').forEach(animateCounter);
    }


    /* ================================================================
       11. APPLIANCE PRESET SELECTOR
       ================================================================ */
    const appliancePreset = document.getElementById('appliancePreset');

    if (appliancePreset) {
        appliancePreset.addEventListener('change', function () {
            const raw = this.value;
            if (!raw) return;

            try {
                const preset = JSON.parse(raw);
                const nameInput  = document.getElementById('appliance_name');
                const powerInput = document.getElementById('power_watts');

                if (nameInput  && preset.name  !== undefined) nameInput.value  = preset.name;
                if (powerInput && preset.watts  !== undefined) powerInput.value = preset.watts;

                // Also update a range if linked
                if (powerInput) {
                    powerInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
            } catch (err) {
                console.warn('EnerSense: Could not parse appliance preset JSON:', err);
            }
        });
    }


    /* ================================================================
       12. AI ADVISOR CHAT
       ================================================================ */
    const advisorForm     = document.getElementById('advisorForm');
    const advisorMessages = document.querySelector('.advisor-messages');
    const advisorInput    = document.getElementById('advisorInput');
    const advisorSendBtn  = document.getElementById('advisorSendBtn');

    // Get user ID from meta tag or data attribute
    function getAdvisorUserId() {
        const meta = document.querySelector('meta[name="user-id"]');
        if (meta) return meta.getAttribute('content');
        const body = document.querySelector('[data-user-id]');
        if (body) return body.getAttribute('data-user-id');
        return null;
    }

    /**
     * Scroll the advisor messages container to the bottom.
     */
    function scrollAdvisorToBottom() {
        if (advisorMessages) {
            advisorMessages.scrollTop = advisorMessages.scrollHeight;
        }
    }

    /**
     * Get the current time in HH:MM format.
     */
    function nowTimeStr() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Append a message bubble to the advisor chat.
     * @param {string} text
     * @param {'bot'|'user'} side
     * @returns {HTMLElement} the bubble wrapper
     */
    function appendMessage(text, side) {
        if (!advisorMessages) return null;

        const isBot = side === 'bot';
        const msg   = document.createElement('div');
        msg.className = 'advisor-message ' + side;

        const avatarIcon = isBot
            ? '<i class="fas fa-robot"></i>'
            : '<i class="fas fa-user"></i>';

        // Basic markdown-style newline handling
        const safeText = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>');

        msg.innerHTML =
            '<div class="advisor-avatar">' + avatarIcon + '</div>' +
            '<div class="advisor-bubble-wrap">' +
            '  <div class="advisor-bubble">' + safeText + '</div>' +
            '  <div class="advisor-time">' + nowTimeStr() + '</div>' +
            '</div>';

        advisorMessages.appendChild(msg);
        scrollAdvisorToBottom();
        return msg;
    }

    /**
     * Show the animated typing indicator.
     * @returns {HTMLElement}
     */
    function showTypingIndicator() {
        if (!advisorMessages) return null;

        const wrapper = document.createElement('div');
        wrapper.className = 'advisor-message bot';
        wrapper.id = 'advisor-typing-indicator';
        wrapper.innerHTML =
            '<div class="advisor-avatar"><i class="fas fa-robot"></i></div>' +
            '<div class="advisor-bubble-wrap">' +
            '  <div class="advisor-typing">' +
            '    <div class="typing-dot"></div>' +
            '    <div class="typing-dot"></div>' +
            '    <div class="typing-dot"></div>' +
            '  </div>' +
            '</div>';

        advisorMessages.appendChild(wrapper);
        scrollAdvisorToBottom();
        return wrapper;
    }

    /**
     * Remove the typing indicator if present.
     */
    function removeTypingIndicator() {
        const indicator = document.getElementById('advisor-typing-indicator');
        if (indicator) indicator.remove();
    }

    /**
     * Send a question to the backend and display the answer.
     * @param {string} questionText
     */
    function sendAdvisorQuestion(questionText) {
        if (!questionText || !questionText.trim()) return;

        const userId = getAdvisorUserId();

        // Disable input & button
        if (advisorInput)   advisorInput.disabled   = true;
        if (advisorSendBtn) advisorSendBtn.disabled = true;

        // Add user message
        appendMessage(questionText.trim(), 'user');

        // Clear input
        if (advisorInput) advisorInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        fetch('/api/advisor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: questionText.trim(), user_id: userId }),
        })
        .then(function (response) {
            if (!response.ok) {
                throw new Error('Server responded with status ' + response.status);
            }
            return response.json();
        })
        .then(function (data) {
            removeTypingIndicator();
            const answer = data.answer || data.response || data.message || 'I could not find an answer. Please try rephrasing your question.';
            appendMessage(answer, 'bot');
        })
        .catch(function (err) {
            console.error('EnerSense Advisor error:', err);
            removeTypingIndicator();
            appendMessage("I'm having trouble connecting right now. Please try again in a moment.", 'bot');
        })
        .finally(function () {
            if (advisorInput) {
                advisorInput.disabled = false;
                advisorInput.focus();
            }
            if (advisorSendBtn) advisorSendBtn.disabled = false;
        });
    }

    // Wire up advisor form submit
    if (advisorForm) {
        advisorForm.addEventListener('submit', function (e) {
            e.preventDefault();
            if (advisorInput) {
                sendAdvisorQuestion(advisorInput.value);
            }
        });
    }

    // Wire up standalone send button (outside form)
    if (advisorSendBtn && !advisorForm) {
        advisorSendBtn.addEventListener('click', function () {
            if (advisorInput) sendAdvisorQuestion(advisorInput.value);
        });
    }

    // Allow Enter key in textarea (Shift+Enter for newline)
    if (advisorInput) {
        advisorInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendAdvisorQuestion(this.value);
            }
        });
    }

    // Suggested questions (pill buttons)
    document.querySelectorAll('.suggested-q').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const question = this.getAttribute('data-question') || this.textContent.trim();
            if (advisorInput) {
                advisorInput.value = question;
                advisorInput.focus();
            }
            // Optionally auto-send
            if (this.getAttribute('data-autosend') === 'true') {
                sendAdvisorQuestion(question);
            }
        });
    });

    // Initial scroll to bottom if there are existing messages
    scrollAdvisorToBottom();


    /* ================================================================
       13. RANGE SLIDER SYNC
       ================================================================ */
    document.querySelectorAll('input[type="range"][data-display-id]').forEach(function (slider) {
        const displayId = slider.getAttribute('data-display-id');
        const inputId   = slider.getAttribute('data-input-id');
        const decimals  = parseInt(slider.getAttribute('data-decimals') || '0', 10);
        const prefix    = slider.getAttribute('data-prefix') || '';
        const suffix    = slider.getAttribute('data-suffix') || '';

        const displayEl = displayId ? document.getElementById(displayId) : null;
        const inputEl   = inputId   ? document.getElementById(inputId)   : null;

        function syncDisplay() {
            const val = parseFloat(slider.value).toFixed(decimals);
            if (displayEl) displayEl.textContent = prefix + val + suffix;
            if (inputEl)   inputEl.value = val;
        }

        slider.addEventListener('input', syncDisplay);
        slider.addEventListener('change', syncDisplay);

        // If there's a linked number input, sync back to slider
        if (inputEl) {
            inputEl.addEventListener('input', function () {
                const v = parseFloat(this.value);
                if (!isNaN(v)) {
                    slider.value = v;
                    if (displayEl) displayEl.textContent = prefix + v.toFixed(decimals) + suffix;
                }
            });
        }

        // Initial sync
        syncDisplay();
    });


    /* ================================================================
       14. TABLE ROW CLICK NAVIGATION
       ================================================================ */
    document.querySelectorAll('tr[data-href]').forEach(function (row) {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function (e) {
            // Don't navigate if a button/link inside was clicked
            if (e.target.closest('a, button, .btn-accent, .btn-glass, .btn-danger, .btn-blue')) return;
            const href = row.getAttribute('data-href');
            if (href) window.location.href = href;
        });
    });


    /* ================================================================
       EXTRA: Animate .animate-in elements via IntersectionObserver
       ================================================================ */
    if ('IntersectionObserver' in window) {
        const animObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    animObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.anim-on-scroll').forEach(function (el) {
            animObserver.observe(el);
        });
    }


    /* ================================================================
       EXTRA: Confirm dangerous actions
       ================================================================ */
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            const msg = el.getAttribute('data-confirm') || 'Are you sure?';
            if (!window.confirm(msg)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });


    /* ================================================================
       EXTRA: Settings tab navigation
       ================================================================ */
    document.querySelectorAll('.settings-nav-item[data-section]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const target = this.getAttribute('data-section');

            // Active state on nav items
            document.querySelectorAll('.settings-nav-item').forEach(function (b) {
                b.classList.remove('active');
            });
            this.classList.add('active');

            // Show / hide sections
            document.querySelectorAll('.settings-section').forEach(function (sec) {
                sec.classList.remove('active');
            });
            const targetSec = document.getElementById(target);
            if (targetSec) targetSec.classList.add('active');
        });
    });

    // Activate first settings section by default
    const firstSettingsBtn = document.querySelector('.settings-nav-item[data-section]');
    if (firstSettingsBtn) firstSettingsBtn.click();


    /* ================================================================
       EXTRA: Bootstrap tooltip initialization
       ================================================================ */
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
            new bootstrap.Tooltip(el, { trigger: 'hover focus' });
        });
    }


    /* ================================================================
       EXTRA: Copy to clipboard buttons
       ================================================================ */
    document.querySelectorAll('[data-copy]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const text = this.getAttribute('data-copy');
            navigator.clipboard.writeText(text).then(function () {
                window.showToast('Copied to clipboard!', 'success', 2500);
            }).catch(function () {
                window.showToast('Could not copy to clipboard.', 'danger', 3000);
            });
        });
    });

}); // END DOMContentLoaded
