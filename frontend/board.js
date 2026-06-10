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
                : `Eval: ${ev.value > 0 ? '+' : ''}${(ev.value/100).toFixed(1)}`;
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