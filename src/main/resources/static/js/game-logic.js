/* src/main/resources/static/js/game-logic.js */

const API_BASE = '/api/sessions';

const GameLogic = {
    // HOST: Create a new session
    async createSession(quizId, token) {
        if (!token) {
            throw new Error("You must provide a JWT Token to host!");
        }

        const response = await fetch(API_BASE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token // <--- THIS IS KEY
            },
            body: JSON.stringify({ quizId: quizId })
        });

        if (!response.ok) {
            // Helper to read the error message from server
            const text = await response.text();
            throw new Error("Server Error: " + text);
        }

        return await response.json();
    },

    // HOST: Start the game
    async startGame(sessionId, token) {
        const response = await fetch(`${API_BASE}/${sessionId}/start`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });
        if (!response.ok) throw new Error("Failed to start game");
        return await response.json();
    },

    async endGame(sessionId, token) {
        const response = await fetch(`${API_BASE}/${sessionId}/end`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || "Failed to end game");
        }

        return await response.json();
    },

    async nextQuestion(sessionId, token) {
        const response = await fetch(`${API_BASE}/${sessionId}/next-question`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!response.ok) throw new Error("Failed to load question");
    },

    async revealAnswer(sessionId, token) {
        const response = await fetch(`${API_BASE}/${sessionId}/reveal-answer`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!response.ok) throw new Error("Failed to reveal answer");
    },

    async getLeaderboard(sessionId) {
        const response = await fetch(`${API_BASE}/${sessionId}/leaderboard`);
        if (!response.ok) throw new Error("Failed to fetch leaderboard");
        return await response.json();
    },

    // PLAYER: Join a session
    async joinSession(pin, nickname) {
        const response = await fetch(`${API_BASE}/join`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gamePin: pin, nickname: nickname })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || "Failed to join");
        }
        return await response.json();
    },

    async submitAnswer(sessionId, playerId, questionId, optionId) {
        // Construct the DTO.Request
        const payload = {
            playerId: playerId,
            questionId: questionId,
            selectedOptionId: optionId
        };

        const response = await fetch(`${API_BASE}/${sessionId}/submit-answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const txt = await response.text();
            throw new Error(txt); // e.g. "Time limit exceeded"
        }
        return await response.json(); // Returns { message, scoreAwarded, totalScore, isCorrect }
    }
};

const UI = {
    // Helper to switch visible screens (divs)
    showScreen(screenId) {
        document.querySelectorAll('.card > div').forEach(div => div.classList.add('hidden'));
        document.getElementById(screenId).classList.remove('hidden');
    },

    // Helper to add a player badge to the grid
    addPlayerBadge(nickname) {
        const grid = document.getElementById('playerGrid');
        if (!document.getElementById(`badge-${nickname}`)) {
            const badge = document.createElement('div');
            badge.className = 'player-badge';
            badge.id = `badge-${nickname}`;
            badge.innerText = nickname;
            grid.appendChild(badge);
            this.updateCount(1);
        }
    },

    // Helper to remove a player badge
    removePlayerBadge(nickname) {
        const badge = document.getElementById(`badge-${nickname}`);
        if (badge) {
            badge.remove();
            this.updateCount(-1);
        }
    },

    updateCount(change) {
        const countEl = document.getElementById('playerCount');
        if (countEl) {
            let current = parseInt(countEl.innerText) || 0;
            countEl.innerText = Math.max(0, current + change);
        }
    }
};

// UI Helpers for Gameplay
const GameUI = {
    // Render the 4 buttons (Used by both Host and Player)
    renderOptions(options, isHost, onOptionClick) {
        const grid = document.getElementById(isHost ? 'hostOptionGrid' : 'playerOptionGrid');
        grid.innerHTML = ''; // Clear old buttons

        options.forEach((opt, index) => {
            const btn = document.createElement('button');
            btn.className = `option-btn opt-${index % 4}`; // Assign colors 0-3

            // Host sees text, Player sees text (or just shapes if you want hard mode)
            btn.innerText = opt.text;
            btn.dataset.id = opt.id;

            if (!isHost) {
                btn.onclick = () => onOptionClick(opt.id);
            }
            grid.appendChild(btn);
        });
    },

    startTimer(durationSeconds, elementId) {
        const bar = document.getElementById(elementId);
        if (!bar) return;

        bar.style.transition = 'none';
        bar.style.width = '100%';

        // Force reflow
        void bar.offsetWidth;

        bar.style.transition = `width ${durationSeconds}s linear`;
        bar.style.width = '0%';
    }
};