/**
 * EduGenie – AI Educational Assistant Frontend Logic
 * Pure Vanilla JavaScript (Modular, Clean, Accessible)
 */

// ============================================================================
// Global State & Configuration
// ============================================================================
const CONFIG = {
    API_BASE: ''
};

const STATE = {
    currentView: 'home',
    activeQuiz: null,            // Holds generated quiz data
    quizAnswers: {},             // Map of question_id -> selected_option
    currentChatHistory: [],
    activities: [],
    currentActivityFilter: 'all',
    lastSummaryResult: null,
    lastLearningPath: null
};

// ============================================================================
// Initialization & Lifecycle
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupEventListeners();
    checkSystemHealth();
    fetchRecentActivity();

    // Auto-update character counts
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('input', () => {
            const count = chatInput.value.length;
            document.getElementById('chat-char-count').innerText = `${count} / 1000 characters`;
        });
    }
});

function setupEventListeners() {
    // Mobile menu toggle
    const mobileBtn = document.getElementById('mobile-menu-btn');
    if (mobileBtn) {
        mobileBtn.addEventListener('click', toggleMobileMenu);
    }
}

// ============================================================================
// Navigation & View Switching
// ============================================================================
function switchView(viewName) {
    if (!viewName) return;
    STATE.currentView = viewName;

    // Update Nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('data-view') === viewName) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Update View Sections
    document.querySelectorAll('.view-section').forEach(sec => {
        sec.classList.remove('active');
    });

    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) {
        targetSection.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Close mobile menu if open
    const navMenu = document.getElementById('nav-menu');
    if (navMenu && navMenu.classList.contains('mobile-open')) {
        navMenu.classList.remove('mobile-open');
    }

    // Refresh activities if activity view opened
    if (viewName === 'activity' || viewName === 'home') {
        fetchRecentActivity();
    }
}

function toggleMobileMenu() {
    const navMenu = document.getElementById('nav-menu');
    if (navMenu) {
        navMenu.classList.toggle('mobile-open');
    }
}

// ============================================================================
// Theme Management (Light / Dark)
// ============================================================================
function initTheme() {
    const savedTheme = localStorage.getItem('edugenie_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('edugenie_theme', next);
    showToast(`Switched to ${next} theme`, 'info');
}

// ============================================================================
// Backend & AI Health Check
// ============================================================================
async function checkSystemHealth() {
    const indicator = document.getElementById('system-status-indicator');
    const label = document.getElementById('status-text');

    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/health`);
        if (response.ok) {
            const data = await response.json();
            indicator.className = 'status-indicator online';
            label.innerText = data.gemini_configured ? 'AI Ready' : 'AI Offline';
            indicator.title = `EduGenie v${data.version} | DB: Connected | AI: ${data.gemini_configured ? 'Active' : 'Missing Key'}`;
        } else {
            throw new Error('Health check failed');
        }
    } catch (err) {
        indicator.className = 'status-indicator offline';
        label.innerText = 'Offline';
        indicator.title = 'Cannot connect to backend server. Make sure FastAPI is running.';
    }
}

// ============================================================================
// 1. ASK AI (CHAT FEATURE)
// ============================================================================
async function submitChat() {
    const input = document.getElementById('chat-input');
    const question = input.value.trim();

    if (!question) {
        showToast('Please enter a question first.', 'error');
        input.focus();
        return;
    }

    const submitBtn = document.getElementById('chat-submit-btn');
    setButtonLoading(submitBtn, true, 'Thinking...');

    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to get answer from AI service.');
        }

        // Hide empty state
        const emptyState = document.getElementById('chat-empty-state');
        if (emptyState) emptyState.classList.add('hidden');

        // Render response card
        renderChatResponse(data);
        input.value = '';
        document.getElementById('chat-char-count').innerText = '0 / 1000 characters';
        showToast('Answer received!', 'success');

        // Refresh activity preview in background
        fetchRecentActivity();

    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(submitBtn, false, 'Ask AI');
    }
}

function renderChatResponse(chatData) {
    const stream = document.getElementById('chat-stream');

    const card = document.createElement('div');
    card.className = 'chat-bubble-card';

    const takeawaysHtml = (chatData.key_takeaways && chatData.key_takeaways.length > 0)
        ? `
        <div class="takeaways-container">
            <div class="takeaways-title">📌 Key Takeaways</div>
            <ul class="takeaways-list">
                ${chatData.key_takeaways.map(pt => `<li>${escapeHtml(pt)}</li>`).join('')}
            </ul>
        </div>
        ` : '';

    const explanationHtml = chatData.explanation
        ? `
        <div class="chat-explanation-block">
            <div class="chat-explanation-title">💡 Simplified Explanation</div>
            <div class="chat-explanation-text">${escapeHtml(chatData.explanation)}</div>
        </div>
        ` : '';

    card.innerHTML = `
        <div class="chat-q-header">
            <div class="user-avatar">Q</div>
            <div class="chat-q-text">${escapeHtml(chatData.question)}</div>
        </div>
        <div class="chat-answer-box">
            <div class="chat-answer-title">EduGenie Direct Answer</div>
            <div class="chat-answer-direct">${escapeHtml(chatData.answer)}</div>
        </div>
        ${explanationHtml}
        ${takeawaysHtml}
        <div class="chat-card-footer">
            <span class="chat-timestamp">${formatTime(new Date())}</span>
            <button class="btn btn-sm btn-ghost" onclick="copyText('${escapeQuotes(chatData.answer)}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                Copy Answer
            </button>
        </div>
    `;

    // Prepend new answers at top
    stream.insertBefore(card, stream.firstChild);
}

function fillChatPrompt(text) {
    const input = document.getElementById('chat-input');
    input.value = text;
    document.getElementById('chat-char-count').innerText = `${text.length} / 1000 characters`;
    input.focus();
}

function clearChatInput() {
    const input = document.getElementById('chat-input');
    input.value = '';
    document.getElementById('chat-char-count').innerText = '0 / 1000 characters';
    input.focus();
}

function clearChat() {
    const stream = document.getElementById('chat-stream');
    stream.innerHTML = `
        <div class="empty-state" id="chat-empty-state">
            <div class="empty-state-icon">💡</div>
            <h3>Ready for Your Questions</h3>
            <p>Enter any academic topic or question above to receive a direct answer, clear explanations, and essential takeaways.</p>
        </div>
    `;
    showToast('Chat history cleared', 'info');
}

// ============================================================================
// 2. AI QUIZ GENERATOR
// ============================================================================
function toggleContextAccordion() {
    const container = document.getElementById('quiz-context-container');
    const arrow = document.getElementById('accordion-arrow');
    const isHidden = container.classList.contains('hidden');

    if (isHidden) {
        container.classList.remove('hidden');
        arrow.innerText = '▾';
    } else {
        container.classList.add('hidden');
        arrow.innerText = '▸';
    }
}

function setQuizTopic(topic, difficulty, count) {
    document.getElementById('quiz-topic').value = topic;
    document.getElementById('quiz-difficulty').value = difficulty;
    document.getElementById('quiz-count').value = count;
}

async function generateQuiz(event) {
    if (event) event.preventDefault();

    const topic = document.getElementById('quiz-topic').value.trim();
    const difficulty = document.getElementById('quiz-difficulty').value;
    const question_count = parseInt(document.getElementById('quiz-count').value, 10);
    const text_content = document.getElementById('quiz-context').value.trim() || null;

    if (!topic) {
        showToast('Please enter a quiz topic.', 'error');
        return;
    }

    const generateBtn = document.getElementById('quiz-generate-btn');
    setButtonLoading(generateBtn, true, 'Generating Quiz...');

    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic,
                difficulty,
                question_count,
                text_content
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to generate quiz.');
        }

        STATE.activeQuiz = data;
        STATE.quizAnswers = {};

        renderActiveQuiz(data);
        showToast('Quiz generated successfully!', 'success');

    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(generateBtn, false, 'Generate Quiz');
    }
}

function renderActiveQuiz(quiz) {
    document.getElementById('quiz-setup-panel').classList.add('hidden');
    document.getElementById('quiz-results-panel').classList.add('hidden');
    const activePanel = document.getElementById('quiz-active-panel');
    activePanel.classList.remove('hidden');

    document.getElementById('quiz-active-topic-badge').innerText = quiz.topic;
    document.getElementById('quiz-active-diff-badge').innerText = quiz.difficulty.toUpperCase();
    document.getElementById('quiz-counter-text').innerText = `0 of ${quiz.questions.length} answered`;
    document.getElementById('quiz-progress-bar').style.width = '0%';

    const listContainer = document.getElementById('quiz-questions-list');
    listContainer.innerHTML = '';

    quiz.questions.forEach((q, idx) => {
        const qCard = document.createElement('div');
        qCard.className = 'quiz-question-item';
        qCard.id = `q-card-${q.id}`;

        const optionsHtml = q.options.map((opt, optIdx) => `
            <label class="quiz-option-label" id="opt-label-${q.id}-${optIdx}">
                <input 
                    type="radio" 
                    name="question-${q.id}" 
                    value="${escapeHtml(opt)}" 
                    onchange="selectQuizOption(${q.id}, '${escapeQuotes(opt)}', ${optIdx})"
                >
                <span>${escapeHtml(opt)}</span>
            </label>
        `).join('');

        qCard.innerHTML = `
            <div class="quiz-question-text">
                <span class="gradient-text">Q${idx + 1}.</span> ${escapeHtml(q.question)}
            </div>
            <div class="quiz-options-grid">
                ${optionsHtml}
            </div>
        `;
        listContainer.appendChild(qCard);
    });

    window.scrollTo({ top: activePanel.offsetTop - 80, behavior: 'smooth' });
}

function selectQuizOption(questionId, selectedOption, optIndex) {
    STATE.quizAnswers[questionId] = selectedOption;

    // Highlight selected label visually
    const qCard = document.getElementById(`q-card-${questionId}`);
    if (qCard) {
        qCard.querySelectorAll('.quiz-option-label').forEach(lbl => lbl.classList.remove('selected'));
        const activeLabel = document.getElementById(`opt-label-${questionId}-${optIndex}`);
        if (activeLabel) activeLabel.classList.add('selected');
    }

    // Update progress bar
    const total = STATE.activeQuiz.questions.length;
    const answeredCount = Object.keys(STATE.quizAnswers).length;
    const percent = Math.round((answeredCount / total) * 100);

    document.getElementById('quiz-counter-text').innerText = `${answeredCount} of ${total} answered`;
    document.getElementById('quiz-progress-bar').style.width = `${percent}%`;
}

async function submitQuizAnswers() {
    if (!STATE.activeQuiz) return;

    const total = STATE.activeQuiz.questions.length;
    const answeredCount = Object.keys(STATE.quizAnswers).length;

    if (answeredCount < total) {
        const proceed = confirm(`You have answered ${answeredCount} of ${total} questions. Do you want to submit anyway?`);
        if (!proceed) return;
    }

    const submitBtn = document.getElementById('quiz-submit-btn');
    setButtonLoading(submitBtn, true, 'Evaluating Score...');

    const submissionPayload = {
        topic: STATE.activeQuiz.topic,
        difficulty: STATE.activeQuiz.difficulty,
        questions: STATE.activeQuiz.questions,
        answers: STATE.activeQuiz.questions.map(q => ({
            question_id: q.id,
            selected_answer: STATE.quizAnswers[q.id] || ""
        }))
    };

    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/quiz/evaluate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(submissionPayload)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Failed to evaluate quiz.');
        }

        renderQuizResults(result);
        showToast('Quiz evaluated!', 'success');
        fetchRecentActivity();

    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(submitBtn, false, 'Submit Quiz & View Score');
    }
}

function renderQuizResults(results) {
    document.getElementById('quiz-active-panel').classList.add('hidden');
    const resultsPanel = document.getElementById('quiz-results-panel');
    resultsPanel.classList.remove('hidden');

    document.getElementById('result-score-fraction').innerText = `${results.score}/${results.total_questions}`;
    document.getElementById('result-score-percent').innerText = `${results.percentage}%`;
    document.getElementById('result-feedback-text').innerText = results.feedback;

    const reviewContainer = document.getElementById('quiz-review-container');
    reviewContainer.innerHTML = '';

    results.reviews.forEach((rev, idx) => {
        const reviewCard = document.createElement('div');
        reviewCard.className = `quiz-review-card ${rev.is_correct ? 'correct' : 'incorrect'}`;

        reviewCard.innerHTML = `
            <div class="review-q-title">
                <span>${rev.is_correct ? '✅' : '❌'} Q${idx + 1}: ${escapeHtml(rev.question)}</span>
            </div>
            <div class="review-answers-box">
                <div class="review-ans-item">
                    <strong>Your Choice:</strong> 
                    <span style="color: ${rev.is_correct ? 'var(--success)' : 'var(--danger)'}">
                        ${escapeHtml(rev.selected_answer)}
                    </span>
                </div>
                ${!rev.is_correct ? `
                <div class="review-ans-item">
                    <strong>Correct Answer:</strong> 
                    <span style="color: var(--success); font-weight: 700;">${escapeHtml(rev.correct_answer)}</span>
                </div>` : ''}
            </div>
            <div class="review-explanation">
                <strong>Explanation:</strong> ${escapeHtml(rev.explanation)}
            </div>
        `;
        reviewContainer.appendChild(reviewCard);
    });

    window.scrollTo({ top: resultsPanel.offsetTop - 80, behavior: 'smooth' });
}

function retryCurrentQuiz() {
    if (!STATE.activeQuiz) return;
    STATE.quizAnswers = {};
    renderActiveQuiz(STATE.activeQuiz);
}

function newQuizSetup() {
    document.getElementById('quiz-results-panel').classList.add('hidden');
    document.getElementById('quiz-active-panel').classList.add('hidden');
    document.getElementById('quiz-setup-panel').classList.remove('hidden');
}

function confirmResetQuiz() {
    if (confirm('Are you sure you want to cancel this quiz session?')) {
        newQuizSetup();
    }
}

// ============================================================================
// 3. SMART SUMMARIZER
// ============================================================================
const SUMMARY_SAMPLES = {
    relativity: `Albert Einstein's Theory of Special Relativity, published in 1905, fundamentally transformed modern physics. It establishes two key postulates: first, the laws of physics are identical in all inertial reference frames; second, the speed of light in a vacuum is constant regardless of the motion of the light source or observer. Special relativity leads to remarkable consequences including time dilation, where moving clocks tick slower relative to stationary observers, and length contraction, where moving objects appear shortened in their direction of motion. Furthermore, Einstein formulated the iconic mass-energy equivalence equation, E = mc², demonstrating that mass and energy are interchangeable. This foundational principle forms the theoretical basis for modern nuclear energy, particle accelerators, and astrophysical models of black holes and the universe.`,
    water_cycle: `The hydrologic cycle, commonly known as the water cycle, describes the continuous movement of water on, above, and below the surface of the Earth. Driven primarily by solar energy and gravity, the cycle consists of several key stages: evaporation, condensation, precipitation, transpiration, and collection. Solar radiation heats ocean and surface water, converting liquid into water vapor that rises into the atmosphere. Plants also contribute water vapor through transpiration. As water vapor rises, it cools and condenses to form clouds. When cloud droplets become heavy enough, they fall back to Earth as precipitation in the form of rain, snow, or hail. This water collects in oceans, lakes, rivers, and underground aquifers, maintaining the global climate balance and sustaining terrestrial life.`
};

function fillSummarySample(key) {
    const text = SUMMARY_SAMPLES[key] || '';
    document.getElementById('summary-text').value = text;
    document.getElementById('summary-title').value = key === 'relativity' ? "Einstein's Special Relativity" : "The Water Cycle";
    updateSummaryWordCount();
}

function updateSummaryWordCount() {
    const text = document.getElementById('summary-text').value;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const chars = text.length;
    document.getElementById('summary-metrics').innerText = `${words} words | ${chars} characters`;
}

function clearSummaryInput() {
    document.getElementById('summary-text').value = '';
    document.getElementById('summary-title').value = '';
    updateSummaryWordCount();
    document.getElementById('summary-text').focus();
}

async function submitSummarize() {
    const text = document.getElementById('summary-text').value.trim();
    const title = document.getElementById('summary-title').value.trim() || null;

    if (!text || text.length < 20) {
        showToast('Please enter an educational passage of at least 20 characters.', 'error');
        return;
    }

    const submitBtn = document.getElementById('summary-submit-btn');
    setButtonLoading(submitBtn, true, 'Summarizing...');

    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, title })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to generate summary.');
        }

        STATE.lastSummaryResult = data;
        renderSummaryResult(data);
        showToast('Summary generated successfully!', 'success');
        fetchRecentActivity();

    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(submitBtn, false, 'Summarize');
    }
}

function renderSummaryResult(data) {
    document.getElementById('summary-empty-state').classList.add('hidden');
    const contentBody = document.getElementById('summary-content-body');
    contentBody.classList.remove('hidden');

    // Update metrics
    document.getElementById('metric-orig-words').innerText = `${data.word_count_original} words`;
    document.getElementById('metric-sum-words').innerText = `${data.word_count_summary} words`;
    const reduction = data.word_count_original > 0 
        ? Math.round((1 - (data.word_count_summary / data.word_count_original)) * 100) 
        : 0;
    document.getElementById('metric-reduction').innerText = `${Math.max(0, reduction)}% saved`;

    // Title & Summary Text
    document.getElementById('summary-rendered-title').innerText = data.title || "Passage Summary";
    document.getElementById('summary-rendered-body').innerText = data.summary;

    // Key points
    const pointsList = document.getElementById('summary-rendered-points');
    pointsList.innerHTML = (data.key_points && data.key_points.length > 0)
        ? data.key_points.map(pt => `<li>${escapeHtml(pt)}</li>`).join('')
        : '<li>No key points extracted.</li>';

    // Important Terms
    const termsGrid = document.getElementById('summary-rendered-terms');
    termsGrid.innerHTML = (data.important_terms && data.important_terms.length > 0)
        ? data.important_terms.map(t => `
            <div class="term-card">
                <div class="term-name">📌 ${escapeHtml(t.term)}</div>
                <div class="term-definition">${escapeHtml(t.definition)}</div>
            </div>
        `).join('')
        : '<p class="text-muted">No specific key terms extracted.</p>';
}

function copySummaryToClipboard() {
    if (!STATE.lastSummaryResult) return;
    const res = STATE.lastSummaryResult;
    const fullText = `=== ${res.title || 'Summary'} ===\n\n${res.summary}\n\nKey Points:\n` +
        res.key_points.map(p => `• ${p}`).join('\n');
    copyText(fullText);
}

// ============================================================================
// 4. PERSONALIZED LEARNING PATH
// ============================================================================
function setLpPreset(topic, level, goal, daily_time, duration) {
    document.getElementById('lp-topic').value = topic;
    document.getElementById('lp-level').value = level;
    document.getElementById('lp-goal').value = goal;
    document.getElementById('lp-time').value = daily_time;
    document.getElementById('lp-duration').value = duration;
}

async function generateLearningPath(event) {
    if (event) event.preventDefault();

    const topic = document.getElementById('lp-topic').value.trim();
    const level = document.getElementById('lp-level').value;
    const goal = document.getElementById('lp-goal').value.trim();
    const daily_time = parseInt(document.getElementById('lp-time').value, 10);
    const duration = document.getElementById('lp-duration').value;

    if (!topic || !goal) {
        showToast('Please specify both a topic and your goal.', 'error');
        return;
    }

    const submitBtn = document.getElementById('lp-submit-btn');
    setButtonLoading(submitBtn, true, 'Building Roadmap...');

    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/learning-path`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic,
                level,
                goal,
                daily_time,
                duration
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to create learning path.');
        }

        STATE.lastLearningPath = data;
        renderLearningPath(data);
        showToast('Learning roadmap ready!', 'success');
        fetchRecentActivity();

    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(submitBtn, false, 'Create Learning Path');
    }
}

function renderLearningPath(data) {
    document.getElementById('lp-empty-state').classList.add('hidden');
    const panel = document.getElementById('lp-result-panel');
    panel.classList.remove('hidden');

    document.getElementById('lp-badge-topic').innerText = data.topic;
    document.getElementById('lp-badge-level').innerText = data.level.toUpperCase();
    document.getElementById('lp-badge-duration').innerText = data.duration;
    document.getElementById('lp-badge-time').innerText = `${data.daily_time} min/day`;

    document.getElementById('lp-render-topic-title').innerText = `${data.topic} Roadmap`;
    document.getElementById('lp-render-overview').innerText = data.overview;

    const timeline = document.getElementById('lp-timeline-list');
    timeline.innerHTML = '';

    data.roadmap.forEach((stage, idx) => {
        const step = document.createElement('div');
        step.className = 'timeline-step';

        const topicsPills = (stage.topics || []).map(t => `<span class="topic-pill">${escapeHtml(t)}</span>`).join('');
        const objectivesList = (stage.learning_objectives || []).map(obj => `<li>${escapeHtml(obj)}</li>`).join('');

        step.innerHTML = `
            <div class="timeline-marker"></div>
            <div class="timeline-card">
                <div class="timeline-period-badge">${escapeHtml(stage.period)}</div>
                <h4 class="timeline-stage-title">${escapeHtml(stage.title)}</h4>
                
                <div class="timeline-details-grid">
                    <div class="timeline-detail-box">
                        <div class="detail-box-label">Core Concepts</div>
                        <div class="timeline-topics-pills">${topicsPills}</div>
                    </div>
                    <div class="timeline-detail-box">
                        <div class="detail-box-label">Learning Objectives</div>
                        <ul style="font-size: 0.85rem; padding-left: 1rem; color: var(--text-secondary);">
                            ${objectivesList}
                        </ul>
                    </div>
                </div>

                <div class="timeline-details-grid">
                    <div class="timeline-detail-box">
                        <div class="detail-box-label">Suggested Practice</div>
                        <p style="font-size: 0.85rem; color: var(--text-secondary);">${escapeHtml(stage.suggested_practice)}</p>
                    </div>
                    <div class="timeline-detail-box">
                        <div class="detail-box-label">Mini Project</div>
                        <p style="font-size: 0.85rem; color: var(--text-secondary); font-weight: 600;">🛠️ ${escapeHtml(stage.mini_project)}</p>
                    </div>
                </div>

                <div class="timeline-next-box">
                    <span>➡️ <strong>Next Step:</strong> ${escapeHtml(stage.recommended_next_step)}</span>
                </div>
            </div>
        `;
        timeline.appendChild(step);
    });

    window.scrollTo({ top: panel.offsetTop - 80, behavior: 'smooth' });
}

function printOrExportRoadmap() {
    window.print();
}

// ============================================================================
// 5. RECENT ACTIVITY FEED
// ============================================================================
async function fetchRecentActivity(forceToast = false) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/activity?limit=15`);
        if (response.ok) {
            const data = await response.json();
            STATE.activities = data.activities || [];
            renderActivityPreview(STATE.activities);
            renderFullActivityFeed(STATE.activities);
            if (forceToast) showToast('Activity log updated', 'info');
        }
    } catch (err) {
        console.warn('Could not fetch recent activity:', err);
    }
}

function renderActivityPreview(activities) {
    const previewContainer = document.getElementById('home-activity-list');
    if (!previewContainer) return;

    if (!activities || activities.length === 0) {
        previewContainer.innerHTML = `
            <div class="activity-item">
                <div class="activity-main">
                    <div class="activity-icon-badge">🚀</div>
                    <div class="activity-info">
                        <div class="activity-title">Welcome to EduGenie!</div>
                        <div class="activity-detail">Start by asking a question or generating a quiz to see your activity here.</div>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    const previewItems = activities.slice(0, 3);
    previewContainer.innerHTML = previewItems.map(item => getActivityItemHtml(item)).join('');
}

function renderFullActivityFeed(activities) {
    const fullFeed = document.getElementById('activity-full-feed');
    if (!fullFeed) return;

    const filtered = (STATE.currentActivityFilter === 'all')
        ? activities
        : activities.filter(a => a.type === STATE.currentActivityFilter);

    if (filtered.length === 0) {
        fullFeed.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <h3>No activity found</h3>
                <p>No activity records matching this filter.</p>
            </div>
        `;
        return;
    }

    fullFeed.innerHTML = filtered.map(item => getActivityItemHtml(item)).join('');
}

function filterActivity(type, btnElement) {
    STATE.currentActivityFilter = type;
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');
    renderFullActivityFeed(STATE.activities);
}

function getActivityItemHtml(item) {
    let icon = '💬';
    let badgeClass = 'icon-chat';
    if (item.type === 'quiz') { icon = '🎯'; badgeClass = 'icon-quiz'; }
    else if (item.type === 'summary') { icon = '📑'; badgeClass = 'icon-summary'; }
    else if (item.type === 'learning_path') { icon = '🗺️'; badgeClass = 'icon-learning'; }

    return `
        <div class="activity-item">
            <div class="activity-main">
                <div class="activity-icon-badge ${badgeClass}">${icon}</div>
                <div class="activity-info">
                    <div class="activity-title">${escapeHtml(item.title)}</div>
                    <div class="activity-detail">${escapeHtml(item.detail)}</div>
                </div>
            </div>
            <div class="activity-time">${formatRelativeTime(item.created_at)}</div>
        </div>
    `;
}

// ============================================================================
// Utility Helpers
// ============================================================================
function setButtonLoading(btn, isLoading, loadingText = 'Processing...') {
    if (!btn) return;
    btn.disabled = isLoading;
    const textSpan = btn.querySelector('.btn-text');
    if (textSpan) {
        textSpan.innerText = loadingText;
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `
        <span>${icon}</span>
        <span class="toast-text">${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 250);
    }, 4000);
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Could not copy to clipboard', 'error');
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function escapeQuotes(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function formatTime(dateObj) {
    return new Intl.DateTimeFormat('en-US', {
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
    }).format(dateObj);
}

function formatRelativeTime(isoString) {
    if (!isoString) return '';
    try {
        const date = new Date(isoString);
        const now = new Date();
        const diffSec = Math.floor((now - date) / 1000);

        if (diffSec < 60) return 'Just now';
        if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
        if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
        return `${Math.floor(diffSec / 86400)}d ago`;
    } catch {
        return '';
    }
}
