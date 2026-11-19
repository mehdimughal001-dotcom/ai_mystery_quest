let currentCase = null;
let currentHintsUsed = 0;
let totalScore = parseInt(localStorage.getItem("mq_score") || "0", 10);
let casesSolved = parseInt(localStorage.getItem("mq_solved") || "0", 10);
let totalHints = parseInt(localStorage.getItem("mq_hints") || "0", 10);
let caseHistory = JSON.parse(localStorage.getItem("mq_history") || "[]");
let isCaseSolved = false;

// DOM Elements
const newCaseBtn = document.getElementById("newCaseBtn");
const loader = document.getElementById("loader");
const gameBoard = document.getElementById("gameBoard");
const getHintBtn = document.getElementById("getHintBtn");
const hintsContainer = document.getElementById("hintsContainer");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatWindow = document.getElementById("chatWindow");
const solveForm = document.getElementById("solveForm");
const feedbackBanner = document.getElementById("feedbackBanner");

function updateStatsUI() {
    document.getElementById("scoreDisplay").textContent = totalScore;
    document.getElementById("solvedDisplay").textContent = casesSolved;
    document.getElementById("hintsUsedDisplay").textContent = totalHints;

    const historyList = document.getElementById("historyList");
    if (caseHistory.length === 0) {
        historyList.innerHTML = `<p class="muted">No cases completed yet. Generate a case to begin your career.</p>`;
        return;
    }

    historyList.innerHTML = caseHistory.map(item => `
        <div class="history-item">
            <div>
                <strong>${item.title}</strong> (${item.difficulty}) — Culprit: <em>${item.culprit}</em>
            </div>
            <span>+${item.points} pts</span>
        </div>
    `).join("");
}

function saveProgress() {
    localStorage.setItem("mq_score", totalScore);
    localStorage.setItem("mq_solved", casesSolved);
    localStorage.setItem("mq_hints", totalHints);
    localStorage.setItem("mq_history", JSON.stringify(caseHistory));
    updateStatsUI();
}

// Generate New Case
newCaseBtn.addEventListener("click", async () => {
    const theme = document.getElementById("themeSelect").value;
    const difficulty = document.getElementById("difficultySelect").value;

    loader.classList.remove("hidden");
    gameBoard.classList.add("hidden");
    feedbackBanner.classList.add("hidden");
    hintsContainer.innerHTML = "";
    currentHintsUsed = 0;
    isCaseSolved = false;

    try {
        const res = await fetch("/api/generate-case", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme, difficulty })
        });
        const data = await res.json();

        if (data.status === "success") {
            currentCase = data.case;
            currentCase.difficulty = difficulty;
            renderCase(currentCase);
        } else {
            alert("Error generating case.");
        }
    } catch (err) {
        alert("Network error connecting to server.");
    } finally {
        loader.classList.add("hidden");
    }
});

function renderCase(caseData) {
    document.getElementById("caseTitle").textContent = caseData.title;
    document.getElementById("caseSetting").textContent = caseData.setting;
    document.getElementById("caseSummary").textContent = caseData.summary;

    const statusBadge = document.getElementById("caseStatusBadge");
    statusBadge.textContent = "ACTIVE INVESTIGATION";
    statusBadge.className = "status-pill active";

    // Render Suspects
    const suspectsList = document.getElementById("suspectsList");
    const suspectSelect = document.getElementById("suspectSelect");
    suspectsList.innerHTML = "";
    suspectSelect.innerHTML = `<option value="">-- Choose Suspect --</option>`;

    caseData.suspects.forEach(s => {
        suspectsList.innerHTML += `
            <div class="suspect-item">
                <h4>${s.name}</h4>
                <div class="suspect-role">${s.role}</div>
                <p><strong>Alibi:</strong> ${s.alibi}</p>
            </div>
        `;
        suspectSelect.innerHTML += `<option value="${s.name}">${s.name} (${s.role})</option>`;
    });

    // Render Evidence
    const evidenceList = document.getElementById("evidenceList");
    evidenceList.innerHTML = caseData.evidence.map(item => `<li>${item}</li>`).join("");

    // Render Puzzle
    document.getElementById("puzzleQuestion").textContent = caseData.puzzle.question;
    document.getElementById("puzzleInput").value = "";

    // Reset Chat
    chatWindow.innerHTML = `<div class="chat-msg ai">Partner online. Ready to investigate "${caseData.title}".</div>`;

    gameBoard.classList.remove("hidden");
}

// Request AI Hint
getHintBtn.addEventListener("click", async () => {
    if (!currentCase || isCaseSolved) return;

    currentHintsUsed++;
    totalHints++;
    totalScore = Math.max(0, totalScore - 15);
    saveProgress();

    getHintBtn.disabled = true;
    getHintBtn.textContent = "Analyzing clues...";

    try {
        const res = await fetch("/api/hint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ case: currentCase, hint_level: currentHintsUsed })
        });
        const data = await res.json();
        if (data.status === "success") {
            hintsContainer.innerHTML += `<div class="hint-item"><strong>Hint #${currentHintsUsed}:</strong> ${data.hint}</div>`;
        }
    } catch (err) {
        hintsContainer.innerHTML += `<div class="hint-item">Unable to fetch hint right now.</div>`;
    } finally {
        getHintBtn.disabled = false;
        getHintBtn.textContent = "💡 Request AI Hint (-15 pts)";
    }
});

// Ask Detective AI Chat
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentCase) return;

    const question = chatInput.value.trim();
    if (!question) return;

    chatWindow.innerHTML += `<div class="chat-msg user">${question}</div>`;
    chatInput.value = "";
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, case: currentCase })
        });
        const data = await res.json();
        const reply = data.reply || "No response from partner.";
        chatWindow.innerHTML += `<div class="chat-msg ai">${reply}</div>`;
    } catch (err) {
        chatWindow.innerHTML += `<div class="chat-msg ai">Connection lost with Detective AI.</div>`;
    }
    chatWindow.scrollTop = chatWindow.scrollHeight;
});

// Submit Final Verdict
solveForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentCase || isCaseSolved) return;

    const suspect = document.getElementById("suspectSelect").value;
    const puzzle_answer = document.getElementById("puzzleInput").value;

    try {
        const res = await fetch("/api/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ suspect, puzzle_answer, case: currentCase })
        });
        const data = await res.json();

        feedbackBanner.classList.remove("hidden");
        if (data.solved) {
            isCaseSolved = true;
            const pointsEarned = Math.max(25, 100 - (currentHintsUsed * 15));
            totalScore += pointsEarned;
            casesSolved += 1;

            caseHistory.unshift({
                title: currentCase.title,
                difficulty: currentCase.difficulty,
                culprit: currentCase.culprit,
                points: pointsEarned
            });
            saveProgress();

            const statusBadge = document.getElementById("caseStatusBadge");
            statusBadge.textContent = "CASE CLOSED";
            statusBadge.className = "status-pill solved";

            feedbackBanner.className = "feedback-banner success";
            feedbackBanner.innerHTML = `<strong>${data.message} (+${pointsEarned} pts)</strong><br><br>${data.explanation}`;
        } else {
            feedbackBanner.className = "feedback-banner error";
            feedbackBanner.textContent = data.message;
        }
    } catch (err) {
        alert("Error submitting verdict.");
    }
});

// Initialize stats on load
updateStatsUI();
