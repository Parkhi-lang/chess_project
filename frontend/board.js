// board.js — Chess Engine Frontend
// Talks to our Django REST API

// ── CONFIG ──────────────────────────────────────
const API_BASE = 'http://127.0.0.1:8000/api';

// Unicode chess pieces
// Key format: 'ColorPiece' e.g. 'whitePawn'
const PIECES = {
    whiteKing: '♔', whiteQueen: '♕',
    whiteRook: '♖', whiteBishop: '♗',
    whiteKnight: '♘', whitePawn: '♙',
    blackKing: '♚', blackQueen: '♛',
    blackRook: '♜', blackBishop: '♝',
    blackKnight: '♞', blackPawn: '♟',
};

// Captured piece symbols for display
const PIECE_SYMBOLS = {
    King: '♔', Queen: '♕', Rook: '♖',
    Bishop: '♗', Knight: '♘', Pawn: '♙'
};

// ── STATE ────────────────────────────────────────
let gameId = null;   // current game UUID
let selectedSquare = null;  // currently selected square e.g. 'e2'
let legalMoves = [];     // legal moves for selected piece
let currentTurn = 'white';
let gameOver = false;
let clockInterval = null;   // setInterval reference
let whiteClock = 0;      // seconds remaining
let blackClock = 0;      // seconds remaining
let moveHistory = [];     // list of moves for display
let capturedByWhite = [];   // pieces white captured
let capturedByBlack = [];   // pieces black captured
let lastMove = null;   // {from, to} for highlighting


// ── SETUP SCREEN ─────────────────────────────────

document.getElementById('start-btn')
    .addEventListener('click', startGame);

async function startGame() {
    const whiteName = document.getElementById('white-name').value || 'Player 1';
    const blackName = document.getElementById('black-name').value || 'Player 2';
    const timeControl = parseInt(document.getElementById('time-control').value);
    const increment = parseInt(document.getElementById('increment').value);

    try {
        // POST to /api/game/new/
        const response = await fetch(`${API_BASE}/game/new/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                white_player: whiteName,
                black_player: blackName,
                time_control: timeControl,
                increment: increment
            })
        });

        const data = await response.json();
        gameId = data.game_id;

        // Update player name displays
        document.getElementById('white-name-display').textContent = whiteName;
        document.getElementById('black-name-display').textContent = blackName;

        // Initialize clocks
        whiteClock = timeControl * 60;
        blackClock = timeControl * 60;
        updateClockDisplay('white', whiteClock);
        updateClockDisplay('black', blackClock);

        // Switch screens
        document.getElementById('setup-screen').classList.add('hidden');
        document.getElementById('game-screen').classList.remove('hidden');

        // Render initial board
        renderBoard(data.board.board);
        updateTurnIndicator('white');
        startClock('white');

    } catch (err) {
        alert('Failed to start game. Is the server running?');
        console.error(err);
    }
}


// ── BOARD RENDERING ──────────────────────────────

function renderBoard(boardData) {
    /**
     * boardData: array of {square, piece, color}
     * e.g. [{square: 'e2', piece: 'Pawn', color: 'white'}, ...]
     * We build an 8x8 grid of squares
     */

    const board = document.getElementById('chess-board');
    board.innerHTML = ''; // clear existing board

    // Build a lookup: square → piece info
    // e.g. {'e2': {piece: 'Pawn', color: 'white'}}
    const pieceMap = {};
    boardData.forEach(p => {
        pieceMap[p.square] = { piece: p.piece, color: p.color };
    });

    // Render row 8 to row 1 (top to bottom)
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const ranks = [8, 7, 6, 5, 4, 3, 2, 1];

    ranks.forEach((rank, rankIdx) => {
        files.forEach((file, fileIdx) => {
            const square = `${file}${rank}`;

            // Create square div
            const sq = document.createElement('div');
            sq.className = 'square';
            sq.dataset.square = square;

            // Light/dark coloring
            // Square is light if (fileIdx + rankIdx) is even
            sq.classList.add(
                (fileIdx + rankIdx) % 2 === 0 ? 'light' : 'dark'
            );

            // Highlight last move
            if (lastMove &&
                (square === lastMove.from || square === lastMove.to)) {
                sq.classList.add('last-move');
            }

            // Highlight selected square
            if (square === selectedSquare) {
                sq.classList.add('selected');
            }

            // Highlight legal moves
            if (legalMoves.includes(square)) {
                const occupant = pieceMap[square];
                if (occupant) {
                    sq.classList.add('legal-capture');
                } else {
                    sq.classList.add('legal-move');
                }
            }

            // Place piece if one exists on this square
            if (pieceMap[square]) {
                const { piece, color } = pieceMap[square];
                const key = `${color}${piece}`;
                // key e.g. 'whitePawn', 'blackKing'

                const pieceEl = document.createElement('span');
                pieceEl.textContent = PIECES[key] || '?';
                pieceEl.className = `piece-${color}`;
                sq.appendChild(pieceEl);
            }

            // Click handler
            sq.addEventListener('click', () => onSquareClick(square));

            board.appendChild(sq);
        });
    });
}


// ── SQUARE CLICK HANDLER ─────────────────────────

async function onSquareClick(square) {
    if (gameOver) return;

    // Case 1: clicked a legal move square → make the move
    if (legalMoves.includes(square)) {
        await makeMove(selectedSquare, square);
        return;
    }

    // Case 2: clicked selected square again → deselect
    if (square === selectedSquare) {
        selectedSquare = null;
        legalMoves = [];
        renderBoard(await getBoardPieces());
        return;
    }

    // Case 3: clicked a piece → select it and show legal moves
    await selectSquare(square);
}

async function selectSquare(square) {
    /**
     * Fetch legal moves for piece on this square
     * Only allow selecting own pieces on own turn
     */
    try {
        const response = await fetch(
            `${API_BASE}/game/${gameId}/moves/?square=${square}`
        );
        const data = await response.json();

        if (data.legal_moves && data.legal_moves.length > 0) {
            selectedSquare = square;
            legalMoves = data.legal_moves;
        } else {
            selectedSquare = null;
            legalMoves = [];
        }

        renderBoard(await getBoardPieces());

    } catch (err) {
        console.error('Failed to get legal moves:', err);
    }
}


// ── MAKE MOVE ────────────────────────────────────

async function makeMove(fromSquare, toSquare) {
    try {
        const response = await fetch(
            `${API_BASE}/game/${gameId}/move/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_square: fromSquare,
                to_square: toSquare
            })
        });

        const data = await response.json();

        if (!data.success) {
            showStatus(data.error || 'Invalid move', 'error');
            return;
        }

        // Update last move highlight
        lastMove = { from: fromSquare, to: toSquare };

        // Update clocks from server response
        if (data.times) {
            whiteClock = data.times.white;
            blackClock = data.times.black;
        }

        // Add to move history display
        addMoveToHistory(fromSquare, toSquare, data);

        // Track captures
        if (data.board) {
            updateCapturedPieces(data.board.board);
        }

        // Clear selection
        selectedSquare = null;
        legalMoves = [];

        // Re-render board
        if (data.board) {
            renderBoard(data.board.board);
        }

        // Handle game over
        if (data.status !== 'active') {
            handleGameOver(data);
            return;
        }

        // Switch turn
        currentTurn = currentTurn === 'white' ? 'black' : 'white';
        updateTurnIndicator(currentTurn);
        switchClock(currentTurn);

        // Show check notification
        if (data.check) {
            showStatus(
                `${currentTurn.charAt(0).toUpperCase() +
                currentTurn.slice(1)} is in CHECK!`,
                'warning'
            );
        } else {
            showStatus(
                `${currentTurn.charAt(0).toUpperCase() +
                currentTurn.slice(1)}'s turn`
            );
        }

        // Show special move notification
        if (data.special) {
            const specials = {
                castling: '🏰 Castling!',
                en_passant: '⚡ En Passant!',
                promotion: '👑 Pawn Promoted!'
            };
            showStatus(specials[data.special] || data.special);
        }

    } catch (err) {
        console.error('Failed to make move:', err);
    }
}


// ── BOARD STATE HELPER ───────────────────────────

async function getBoardPieces() {
    /**
     * Fetch current board state from API.
     * Returns the board array for renderBoard()
     */
    const response = await fetch(
        `${API_BASE}/game/${gameId}/`
    );
    const data = await response.json();
    return data.board.board;
}


// ── CLOCK SYSTEM ─────────────────────────────────

function startClock(color) {
    /**
     * Start countdown for given color.
     * Runs every 100ms for smooth display.
     */
    stopClock(); // clear any existing interval

    clockInterval = setInterval(() => {
        if (color === 'white') {
            whiteClock -= 0.1;
            updateClockDisplay('white', whiteClock);
            if (whiteClock <= 0) {
                stopClock();
                handleTimeout('white');
            }
        } else {
            blackClock -= 0.1;
            updateClockDisplay('black', blackClock);
            if (blackClock <= 0) {
                stopClock();
                handleTimeout('black');
            }
        }
    }, 100);
}

function stopClock() {
    if (clockInterval) {
        clearInterval(clockInterval);
        clockInterval = null;
    }
}

function switchClock(newColor) {
    stopClock();
    startClock(newColor);
}

function updateClockDisplay(color, seconds) {
    /**
     * Format seconds as MM:SS and update display.
     * e.g. 304.5 → "05:04"
     */
    const el = document.getElementById(`${color}-clock`);
    const secs = Math.max(0, seconds);
    const mins = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);

    // Pad with leading zero: 5 → "05"
    el.textContent =
        `${String(mins).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

    // Flash red when under 30 seconds
    if (secs < 30) {
        el.classList.add('low-time');
    } else {
        el.classList.remove('low-time');
    }
}

function handleTimeout(color) {
    gameOver = true;
    const winner = color === 'white' ? 'black' : 'white';
    showModal(
        '⏰ Time Out!',
        `${color.charAt(0).toUpperCase() + color.slice(1)} ran out of time. ${winner.charAt(0).toUpperCase() + winner.slice(1)} wins!`
    );
}


// ── UI HELPERS ───────────────────────────────────

function updateTurnIndicator(color) {
    document.getElementById('white-bar')
        .classList.toggle('active-turn', color === 'white');
    document.getElementById('black-bar')
        .classList.toggle('active-turn', color === 'black');
}

function showStatus(message, type = 'normal') {
    const el = document.getElementById('status-text');
    el.textContent = message;
    el.style.color = type === 'error' ? '#e74c3c' :
        type === 'warning' ? '#f39c12' :
            '#e2b96f';
}

function addMoveToHistory(from, to, data) {
    /**
     * Add a row to the move history table.
     * Pairs white and black moves on same row.
     */
    const tbody = document.getElementById('moves-body');
    const moveNum = Math.ceil((moveHistory.length + 1) / 2);
    const moveStr = `${from}→${to}`;

    moveHistory.push({ color: currentTurn, move: moveStr });

    if (currentTurn === 'white') {
        // Start new row for white's move
        const row = tbody.insertRow();
        row.insertCell(0).textContent = moveNum;
        row.insertCell(1).textContent = moveStr;
        row.insertCell(2).textContent = '';
    } else {
        // Add black's move to last row
        const lastRow = tbody.rows[tbody.rows.length - 1];
        if (lastRow) {
            lastRow.cells[2].textContent = moveStr;
        }
    }

    // Auto scroll to bottom
    const hist = document.getElementById('move-history');
    hist.scrollTop = hist.scrollHeight;
}

function updateCapturedPieces(boardData) {
    /**
     * Calculate captured pieces by comparing
     * current board vs starting piece counts.
     */
    const startCounts = {
        white: { Pawn: 8, Rook: 2, Knight: 2, Bishop: 2, Queen: 1, King: 1 },
        black: { Pawn: 8, Rook: 2, Knight: 2, Bishop: 2, Queen: 1, King: 1 }
    };

    const currentCounts = { white: {}, black: {} };
    boardData.forEach(({ piece, color }) => {
        currentCounts[color][piece] =
            (currentCounts[color][piece] || 0) + 1;
    });

    // White captured = black pieces missing from board
    capturedByWhite = [];
    Object.entries(startCounts.black).forEach(([piece, count]) => {
        const current = currentCounts.black[piece] || 0;
        const captured = count - current;
        for (let i = 0; i < captured; i++) {
            capturedByWhite.push(PIECE_SYMBOLS[piece]);
        }
    });

    // Black captured = white pieces missing from board
    capturedByBlack = [];
    Object.entries(startCounts.white).forEach(([piece, count]) => {
        const current = currentCounts.white[piece] || 0;
        const captured = count - current;
        for (let i = 0; i < captured; i++) {
            capturedByBlack.push(PIECE_SYMBOLS[piece]);
        }
    });

    document.getElementById('white-captured').textContent =
        capturedByWhite.join('') || '–';
    document.getElementById('black-captured').textContent =
        capturedByBlack.join('') || '–';
}


// ── GAME OVER ────────────────────────────────────

function handleGameOver(data) {
    gameOver = true;
    stopClock();

    const messages = {
        checkmate: `Checkmate! ${data.winner} wins! 🏆`,
        stalemate: `Stalemate! It's a draw! 🤝`,
        timeout: `Time out! ${data.winner} wins! ⏰`,
        resigned: `${data.winner} wins by resignation!`
    };

    const msg = messages[data.status] || 'Game Over';
    showModal('Game Over', msg);

    // Show review button
    document.getElementById('review-btn')
        .classList.remove('hidden');
}

function showModal(title, message) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;
    document.getElementById('modal').classList.remove('hidden');
}


// ── RESIGN ───────────────────────────────────────

document.getElementById('resign-btn')
    .addEventListener('click', async () => {
        if (gameOver) return;
        if (!confirm(`Resign as ${currentTurn}?`)) return;

        try {
            await fetch(`${API_BASE}/game/${gameId}/resign/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ color: currentTurn })
            });

            gameOver = true;
            stopClock();
            const winner = currentTurn === 'white' ? 'black' : 'white';
            showModal('Resignation', `${winner} wins by resignation!`);

        } catch (err) {
            console.error('Failed to resign:', err);
        }
    });


// ── REVIEW ───────────────────────────────────────

document.getElementById('review-btn')
    .addEventListener('click', showReview);

document.getElementById('modal-review')
    .addEventListener('click', () => {
        document.getElementById('modal').classList.add('hidden');
        showReview();
    });

async function showReview() {
    try {
        const response = await fetch(
            `${API_BASE}/game/${gameId}/review/`
        );
        const data = await response.json();
        const review = data.review;

        document.getElementById('game-screen')
            .classList.add('hidden');
        document.getElementById('review-screen')
            .classList.remove('hidden');

        const content = document.getElementById('review-content');
        content.innerHTML = `
            <div class="review-grid">
                <div class="review-stat">
                    <h3>${review.summary.total_moves}</h3>
                    <p>Total Moves</p>
                </div>
                <div class="review-stat">
                    <h3>${review.summary.result}</h3>
                    <p>Result</p>
                </div>
                <div class="review-stat">
                    <h3>${review.white_stats.captures}</h3>
                    <p>White Captures</p>
                </div>
                <div class="review-stat">
                    <h3>${review.black_stats.captures}</h3>
                    <p>Black Captures</p>
                </div>
                <div class="review-stat">
                    <h3>${review.white_stats.avg_move_time}s</h3>
                    <p>White Avg Time</p>
                </div>
                <div class="review-stat">
                    <h3>${review.black_stats.avg_move_time}s</h3>
                    <p>Black Avg Time</p>
                </div>
            </div>

            <div class="pgn-box">
                <strong>PGN:</strong><br>
                ${review.pgn}
            </div>
        `;

    } catch (err) {
        console.error('Failed to load review:', err);
    }
}


// ── NEW GAME ─────────────────────────────────────

document.getElementById('modal-new')
    .addEventListener('click', resetToSetup);

document.getElementById('new-game-btn')
    .addEventListener('click', resetToSetup);

function resetToSetup() {
    // Reset all state
    gameId = null;
    selectedSquare = null;
    legalMoves = [];
    currentTurn = 'white';
    gameOver = false;
    moveHistory = [];
    capturedByWhite = [];
    capturedByBlack = [];
    lastMove = null;

    stopClock();

    // Clear board and history
    document.getElementById('chess-board').innerHTML = '';
    document.getElementById('moves-body').innerHTML = '';
    document.getElementById('white-captured').textContent = '';
    document.getElementById('black-captured').textContent = '';

    // Switch screens
    document.getElementById('modal')
        .classList.add('hidden');
    document.getElementById('review-screen')
        .classList.add('hidden');
    document.getElementById('game-screen')
        .classList.add('hidden');
    document.getElementById('setup-screen')
        .classList.remove('hidden');

    // Hide review button
    document.getElementById('review-btn')
        .classList.add('hidden');
}
// AI Move button
document.getElementById('ai-move-btn')
    .addEventListener('click', async () => {
        if (gameOver) return;

        const difficulty = document.getElementById('ai-difficulty').value;
        showStatus('🤖 Stockfish is thinking...');

        try {
            const response = await fetch(
                `${API_BASE}/game/${gameId}/ai-move/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ difficulty })
            });

            const data = await response.json();

            if (!data.success) {
                showStatus(data.error || 'AI move failed', 'error');
                return;
            }

            // Update board
            lastMove = { from: data.from, to: data.to };
            addMoveToHistory(data.from, data.to, data);

            if (data.board) {
                renderBoard(data.board.board);
                updateCapturedPieces(data.board.board);
            }

            // Show evaluation
            if (data.evaluation) {
                const ev = data.evaluation;
                const evalText = ev.type === 'mate'
                    ? `Mate in ${Math.abs(ev.value)}`
                    : `Eval: ${ev.value > 0 ? '+' : ''}${(ev.value / 100).toFixed(1)}`;
                showStatus(`🤖 Stockfish played ${data.move} (${evalText})`);
            }

            if (data.status !== 'active') {
                handleGameOver(data);
                return;
            }

            currentTurn = currentTurn === 'white' ? 'black' : 'white';
            updateTurnIndicator(currentTurn);
            switchClock(currentTurn);

        } catch (err) {
            showStatus('Failed to get AI move', 'error');
            console.error(err);
        }
    });

