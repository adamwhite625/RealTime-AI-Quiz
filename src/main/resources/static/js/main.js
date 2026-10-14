/* src/main/resources/static/js/main.js */

// Global State
let currentSessionId = null;
let myNickname = null;
let currentHostToken = null;
let myPlayerId = null;
let isLastRound = false;

document.addEventListener('DOMContentLoaded', () => {

    // --- PLAYER PAGE LOGIC ---
    const joinBtn = document.getElementById('btnJoin');
    if (joinBtn) {
        joinBtn.addEventListener('click', async () => {
            const pin = document.getElementById('inputPin').value;
            const nick = document.getElementById('inputNick').value;
            const errorEl = document.getElementById('errorMsg');

            if (!pin || !nick) {
                errorEl.innerText = "Please enter both PIN and Nickname";
                return;
            }

            try {
                // 1. API Call
                const data = await GameLogic.joinSession(pin, nick);

                currentSessionId = data.sessionId;
                myNickname = nick;
                myPlayerId = data.playerId;

                // 2. Update UI
                document.getElementById('displayNick').innerText = nick;
                UI.showScreen('lobbyScreen');

                if (data.currentPlayers && Array.isArray(data.currentPlayers)) {
                    data.currentPlayers.forEach(player => {
                        UI.addPlayerBadge(player.nickname);
                    });
                }

                // 3. Connect WebSocket
                gameSocket.connect(() => {
                    gameSocket.subscribeToSession(currentSessionId, handleGameEvent);
                });

            } catch (err) {
                errorEl.innerText = err.message;
            }
        });
    }

    // --- HOST PAGE LOGIC ---
    const createBtn = document.getElementById('btnCreate');
    if (createBtn) {
        createBtn.addEventListener('click', async () => {
            const quizId = document.getElementById('inputQuizId').value;
            const token = document.getElementById('inputToken').value;
            const errorEl = document.getElementById('hostErrorMsg');

            try {
                // 1. Create Session via API
                currentHostToken = token;
                const data = await GameLogic.createSession(quizId, token);
                currentSessionId = data.sessionId;

                // 2. Update UI
                document.getElementById('displayPin').innerText = data.gamePin;
                UI.showScreen('hostLobbyScreen');

                // 3. Connect WebSocket
                gameSocket.connect(() => {
                    // A. Subscribe to Public Events (Joins, Game State)
                    gameSocket.subscribeToSession(currentSessionId, handleGameEvent);

                    // B. Subscribe to Private Host Events (Answer Counts)
                    gameSocket.subscribeToHost(currentSessionId, handleGameEvent);
                });

            } catch (err) {
                errorEl.innerText = "Error: " + err.message;
            }
        });
    }

    const btnNextQ = document.getElementById('btnStart'); // "Start Game" becomes "Next Question" logic
    if (btnNextQ) {
        btnNextQ.addEventListener('click', async () => {
            try {
                // Determine if we are Starting Game or Moving to Next Question
                // For simplicity, let's assume the Start button calls 'next-question' 
                // OR we add a specific 'btnNextQuestion' in the Host Question Screen
                await GameLogic.nextQuestion(currentSessionId, currentHostToken);
            } catch (err) {
                console.error(err);
            }
        });
    }

    const btnNextRound = document.getElementById('btnNextQuestion');
    if (btnNextRound) {
        btnNextRound.addEventListener('click', async () => {
            if (isLastRound) {
                // 1. END GAME LOGIC
                if (confirm("This will end the game. Are you sure?")) {
                    try {
                        await GameLogic.endGame(currentSessionId, currentHostToken);
                        // UI Update happens in handleGameEvent -> GAME_ENDED
                    } catch (err) {
                        alert("Error ending game: " + err.message);
                    }
                }
            } else {
                // 1. Restore UI State (Hide Leaderboard, Show Stats)
                document.getElementById('hostLeaderboard').classList.add('hidden');
                document.getElementById('hostStatsBox').classList.remove('hidden');
                // 2. NOW it is safe to access hostAnswerCount because we didn't delete it
                document.getElementById('hostAnswerCount').innerText = "0";

                // 3. Clear other UI elements
                document.getElementById('hostQuestionText').innerText = "Loading next question...";
                document.getElementById('hostOptionGrid').innerHTML = "";
                document.getElementById('hostTimer').style.width = "100%";
                document.getElementById('btnEndQuestion').disabled = false;

                // 4. Show the screen
                UI.showScreen('hostQuestionScreen');
                document.getElementById('hostControls').classList.add('hidden');

                try {
                    await GameLogic.nextQuestion(currentSessionId, currentHostToken);
                } catch (err) {
                    console.error("Failed to load next:", err);
                    document.getElementById('hostQuestionText').innerText = "Error: " + err.message;
                }
            }
        });
    }

    const btnEndQ = document.getElementById('btnEndQuestion');
    if (btnEndQ) {
        btnEndQ.addEventListener('click', async () => {
            try {
                await GameLogic.revealAnswer(currentSessionId, currentHostToken);
            } catch (err) {
                console.error(err);
            }
        });
    }

    const endBtn = document.getElementById('btnEnd');
    if (endBtn) {
        endBtn.addEventListener('click', async () => {
            try {
                if (!currentHostToken) return alert("Missing Token");

                await GameLogic.endGame(currentSessionId, currentHostToken);
                console.log("End Game command sent!");
            } catch (err) {
                alert("Could not end game: " + err.message);
            }
        });
    }
});

// --- SHARED EVENT HANDLER ---
function handleGameEvent(event) {
    console.log("Event Received:", event);

    switch (event.type) {
        case 'PLAYER_JOINED':
            UI.addPlayerBadge(event.nickname);
            break;
        case 'PLAYER_LEFT':
            UI.removePlayerBadge(event.nickname);
            break;
        case 'GAME_STARTED': // This is usually the first question
            // We can trigger nextQuestion automatically or wait for host
            break;
        case 'NEXT_QUESTION':
            handleNextQuestion(event);
            break;

        case 'ANSWER_RECEIVED':
            // Update Host Counter
            if (document.getElementById('hostAnswerCount')) {
                // The DTO.HostUpdate has 'answersCount'
                document.getElementById('hostAnswerCount').innerText = event.answersCount;
            }
            break;
        case 'REVEAL_ANSWER':
            // 1. Highlight the correct answer (Host & Player)
            highlightCorrectOption(event.correctOptionId);

            // 2. Show Leaderboard (Host Only - Optional)
            if (document.getElementById('hostQuestionScreen')) {
                renderLeaderboard(event.leaderboard);

                // 3. Enable "Next Question" button
                document.getElementById('hostControls').classList.remove('hidden');
                document.getElementById('btnEndQuestion').disabled = true; // Disable "Stop" button
            }
            break;
        case 'GAME_ENDED':
            // 1. Determine Role
            const isHostEnd = !!document.getElementById('hostGameOverScreen');

            if (isHostEnd) {
                UI.showScreen('hostGameOverScreen');

                // 2. Fetch Final Leaderboard immediately
                GameLogic.getLeaderboard(currentSessionId, currentHostToken).then(leaderboard => {
                    // Reuse our render logic, but target the final div
                    // We can reuse the helper logic or write a custom podium render
                    renderFinalPodium(leaderboard);
                }).catch(err => {
                    document.getElementById('finalLeaderboard').innerText = "Could not load results.";
                });

            } else {
                UI.showScreen('playerGameOverScreen');
            }

            if (typeof gameSocket !== 'undefined') gameSocket.disconnect();
            break;
    }
}

function handleNextQuestion(data) {
    // 1. Check if this is the last question
    isLastRound = (data.currentQuestionNumber === data.totalQuestions);

    // 2. Determine Role and Update UI
    const isHost = !!document.getElementById('hostQuestionScreen');

    if (isHost) {
        // --- HOST VIEW ---
        UI.showScreen('hostQuestionScreen');
        document.getElementById('hostQuestionText').innerText = data.text;
        document.getElementById('qCurrent').innerText = data.currentQuestionNumber;
        document.getElementById('qTotal').innerText = data.totalQuestions;
        document.getElementById('hostAnswerCount').innerText = "0";
        document.getElementById('hostTotalPlayers').innerText = document.getElementById('playerCount').innerText;

        const nextBtn = document.getElementById('btnNextQuestion');
        if (isLastRound) {
            nextBtn.innerText = "Finish Game 🏁";
            nextBtn.style.backgroundColor = "#d9534f"; // Red/Orange for emphasis
        } else {
            nextBtn.innerText = "Next Question ➡";
            nextBtn.style.backgroundColor = "#28a745"; // Green
        }

        // Render Read-Only Options
        GameUI.renderOptions(data.options, true, null);

        // Start Timer
        GameUI.startTimer(data.timeLimitSeconds, 'hostTimer');

    } else {
        // --- PLAYER VIEW ---
        UI.showScreen('playerQuestionScreen');
        document.getElementById('pQNum').innerText = data.currentQuestionNumber;

        // Render Clickable Options
        GameUI.renderOptions(data.options, false, async (selectedOptionId) => {
            // Player Clicked an Option
            try {
                // 1. Disable buttons to prevent double click
                document.querySelectorAll('.option-btn').forEach(b => b.disabled = true);

                // 2. Send API Request
                // (Assuming we saved myPlayerId during Join)
                const result = await GameLogic.submitAnswer(currentSessionId, myPlayerId, data.questionId, selectedOptionId);

                // 3. Show Result Screen
                UI.showScreen('playerResultScreen');

                const msgBox = document.getElementById('resultBox');
                const msgText = document.getElementById('resultMessage');
                const scoreText = document.getElementById('pScore');

                msgText.innerText = result.isCorrect ? "Correct! 🎉" : "Wrong 😞";
                msgBox.className = "feedback-box " + (result.isCorrect ? "feedback-correct" : "feedback-wrong");
                scoreText.innerText = result.totalScore;

            } catch (err) {
                alert("Error: " + err.message);
            }
        });

        // Start Timer
        GameUI.startTimer(data.timeLimitSeconds, 'pTimer');
    }
}

function highlightCorrectOption(correctId) {
    // Select all option buttons
    const buttons = document.querySelectorAll('.option-btn');

    buttons.forEach(btn => {
        // We stored the ID in dataset.id during renderOptions()
        // Note: dataset stores as string, correctId might be number. Use == for safety.
        if (btn.dataset.id == correctId) {
            btn.classList.add('correct'); // Add Green Border/Glow
            btn.style.opacity = "1";
        } else {
            btn.classList.add('dimmed'); // Fade out wrong answers
            btn.disabled = true;
        }
    });
}

function renderLeaderboard(leaderboardData) {
    // 1. Hide Stats, Show Leaderboard
    document.getElementById('hostStatsBox').classList.add('hidden');
    const lbContainer = document.getElementById('hostLeaderboard');
    lbContainer.classList.remove('hidden');

    // 2. Build the HTML
    let html = "<h3>🏆 Top Players</h3><ul style='list-style:none; padding:0;'>";
    leaderboardData.forEach((p, index) => {
        let icon = index === 0 ? "🥇" : index === 1 ? "🥈" : index === 2 ? "🥉" : "🔸";
        html += `<li style="margin:10px 0; font-size:1.2rem; border-bottom:1px solid #eee; padding:5px;">
                    ${icon} <strong>${p.nickname}</strong> 
                    <span style="float:right; font-weight:bold;">${p.score} pts</span>
                 </li>`;
    });
    html += "</ul>";

    lbContainer.innerHTML = html;
}

function renderFinalPodium(leaderboard) {
    const container = document.getElementById('finalLeaderboard');
    if (!leaderboard || leaderboard.length === 0) {
        container.innerHTML = "<p>No scores recorded.</p>";
        return;
    }

    let html = "<ul style='list-style:none; padding:0; text-align:left;'>";
    leaderboard.forEach((p, index) => {
        // Highlight Top 3
        let bgStyle = "";
        let icon = "🔸";
        let fontSize = "1.2rem";

        if (index === 0) { icon = "🥇"; bgStyle = "background:#ffd70033; border:2px solid gold;"; fontSize = "1.5rem"; }
        if (index === 1) { icon = "🥈"; bgStyle = "background:#c0c0c033;"; }
        if (index === 2) { icon = "🥉"; bgStyle = "background:#cd7f3233;"; }

        html += `<li style="padding:10px; margin-bottom:8px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; ${bgStyle}">
                    <span style="font-size:${fontSize}"> ${icon} <strong>${p.nickname}</strong></span>
                    <span style="font-weight:bold; font-size:1.2rem;">${p.score} pts</span>
                 </li>`;
    });
    html += "</ul>";
    container.innerHTML = html;
}