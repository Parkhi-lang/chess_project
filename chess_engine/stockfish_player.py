# chess_engine/stockfish_player.py

from stockfish import Stockfish
import os


class StockfishPlayer:
    """
    Integrates the Stockfish chess engine as an AI opponent.

    Stockfish communicates via UCI protocol (Universal Chess Interface).
    UCI is a standard text-based protocol that all major chess engines use.

    Communication flow:
    ────────────────────────────────────────────────
    Python sends:  position fen <FEN_STRING>
    Python sends:  go movetime 1000
    Stockfish returns: bestmove e2e4

    FEN (Forsyth-Edwards Notation):
    ────────────────────────────────────────────────
    FEN is a single string encoding the complete board state.
    Example starting position FEN:
    rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

    Breaking it down:
    rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR
    → Board position rank by rank (8 to 1)
    → lowercase = black pieces, uppercase = white
    → numbers = consecutive empty squares

    w         → whose turn (w=white, b=black)
    KQkq      → castling rights (K=white kingside etc)
    -         → en passant target square (- if none)
    0         → halfmove clock (for 50-move rule)
    1         → fullmove number
    """

    # Difficulty levels mapped to ELO ratings
    # ELO is the universal chess skill rating system
    DIFFICULTY_LEVELS = {
        'beginner':     800,    # Complete beginner
        'easy':         1100,   # Casual player
        'medium':       1500,   # Club player
        'hard':         1900,   # Strong club player
        'expert':       2300,   # Near master level
        'master':       2700,   # Grandmaster level
    }

    def __init__(self, difficulty='medium', stockfish_path=None):
        """
        Initialize Stockfish engine.

        difficulty: 'beginner', 'easy', 'medium', 'hard', 'expert', 'master'
        stockfish_path: path to stockfish binary
                        auto-detected if None
        """
        self.difficulty   = difficulty
        self.elo          = self.DIFFICULTY_LEVELS.get(difficulty, 1500)
        self.stockfish    = None
        self._initialized = False

        # Auto-detect stockfish binary path
        if stockfish_path is None:
            stockfish_path = self._find_stockfish()

        self._init_engine(stockfish_path)

    def _find_stockfish(self):
        """
        Auto-detect Stockfish binary in common locations.
        Checks project stockfish/ folder first, then system PATH.
        """
        # Common paths to check
        candidates = [
            # Project stockfish folder (Windows)
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'stockfish',
                'stockfish-windows-x86-64.exe'
            ),
            # Project stockfish folder (Linux/Mac)
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'stockfish',
                'stockfish'
            ),
            # System PATH locations
            'stockfish',
            '/usr/bin/stockfish',
            '/usr/local/bin/stockfish',
        ]

        for path in candidates:
            if os.path.isfile(path):
                print(f"Found Stockfish at: {path}")
                return path

        # If not found, try default (might be in PATH)
        return 'stockfish'

    def _init_engine(self, path):
        """Initialize the Stockfish engine with settings."""
        try:
            self.stockfish = Stockfish(
                path=path,
                depth=15,
                # depth: how many moves ahead Stockfish looks
                # 15 = strong but fast enough for real-time play
                # Higher = stronger but slower

                parameters={
                    # Threads: CPU cores to use
                    # 1 is safe for all systems
                    "Threads": 1,

                    # Hash: RAM for position cache in MB
                    # 16MB is fine for casual play
                    "Hash": 16,

                    # UCI_LimitStrength: enable ELO limiting
                    # When True, Stockfish plays at set ELO
                    # When False, plays at full strength
                    "UCI_LimitStrength": True,

                    # UCI_Elo: target playing strength
                    # Range: 1320 to 3190
                    "UCI_Elo": max(1320, min(self.elo, 3190)),

                    # Skill Level: 0-20 (alternative to ELO)
                    # We use ELO instead for more intuitive control
                    "Skill Level": 20,
                }
            )
            self._initialized = True
            print(f"Stockfish initialized — Difficulty: {self.difficulty} (ELO {self.elo})")

        except Exception as e:
            print(f"Warning: Could not initialize Stockfish: {e}")
            print("AI will use random legal moves as fallback")
            self._initialized = False

    # ─────────────────────────────────────────────────
    # CORE INTERFACE
    # ─────────────────────────────────────────────────

    def get_best_move(self, game_state):
        """
        Main method: given a GameState, return the best move.
        Returns (from_square, to_square) e.g. ('e2', 'e4')

        Steps:
        1. Convert our board → FEN string
        2. Send FEN to Stockfish
        3. Get Stockfish's best move
        4. Convert back to our notation
        """
        if not self._initialized:
            return self._random_move(game_state)

        try:
            # Convert our board state to FEN
            fen = self._board_to_fen(game_state)

            # Send position to Stockfish
            self.stockfish.set_fen_position(fen)

            # Get best move
            # Returns string like 'e2e4' or 'e7e8q' (promotion)
            best_move = self.stockfish.get_best_move()

            if best_move is None:
                return self._random_move(game_state)

            # Parse move string
            # Stockfish uses 'e2e4' format (no separator)
            # We need ('e2', 'e4') format
            from_sq = best_move[0:2]   # 'e2'
            to_sq   = best_move[2:4]   # 'e4'
            # best_move[4] would be promotion piece if present

            return (from_sq, to_sq)

        except Exception as e:
            print(f"Stockfish error: {e}")
            return self._random_move(game_state)

    def get_move_evaluation(self, game_state):
        """
        Returns position evaluation from Stockfish.
        Used for post-game analysis.

        Returns dict:
        {
            'type': 'cp',        # centipawns (normal eval)
            'value': 150         # +150 = white is ahead by 1.5 pawns
        }
        or:
        {
            'type': 'mate',
            'value': 3           # checkmate in 3 moves
        }
        """
        if not self._initialized:
            return {'type': 'cp', 'value': 0}

        try:
            fen = self._board_to_fen(game_state)
            self.stockfish.set_fen_position(fen)
            evaluation = self.stockfish.get_evaluation()
            return evaluation
        except Exception:
            return {'type': 'cp', 'value': 0}

    def set_difficulty(self, difficulty):
        """Change difficulty level during a game."""
        if difficulty in self.DIFFICULTY_LEVELS:
            self.difficulty = difficulty
            self.elo        = self.DIFFICULTY_LEVELS[difficulty]
            if self._initialized:
                self.stockfish.update_engine_parameters({
                    "UCI_Elo": max(1320, min(self.elo, 3190))
                })

    # ─────────────────────────────────────────────────
    # FEN CONVERSION
    # ─────────────────────────────────────────────────

    def _board_to_fen(self, game_state):
        """
        Convert our GameState to FEN string.

        FEN format:
        <piece_placement> <active_color> <castling> <en_passant> <halfmove> <fullmove>

        Example:
        rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
        """
        board = game_state.board

        # ── Piece Placement ──
        # Iterate rows 0-7 (rank 8 to rank 1)
        rows = []
        for row in range(8):
            row_str   = ''
            empty_count = 0

            for col in range(8):
                piece = board.get_piece(row, col)

                if piece is None:
                    # Count consecutive empty squares
                    empty_count += 1
                else:
                    # Flush empty count before adding piece
                    if empty_count > 0:
                        row_str    += str(empty_count)
                        empty_count = 0

                    # Get FEN piece character
                    # Uppercase = white, lowercase = black
                    symbol = self._piece_to_fen_char(piece)
                    row_str += symbol

            # Flush remaining empty squares at end of row
            if empty_count > 0:
                row_str += str(empty_count)

            rows.append(row_str)

        piece_placement = '/'.join(rows)

        # ── Active Color ──
        active_color = 'w' if game_state.current_turn == 'white' else 'b'

        # ── Castling Rights ──
        # Check which castling moves are still available
        castling = self._get_castling_fen(game_state)

        # ── En Passant Target ──
        ep_target = '-'
        if game_state.en_passant_target:
            ep_row, ep_col = game_state.en_passant_target
            ep_target = board.coords_to_notation(ep_row, ep_col)

        # ── Move Counters ──
        # Halfmove clock: moves since last capture or pawn move
        # We approximate with 0 (simplification)
        halfmove = 0

        # Fullmove number: increments after black's move
        fullmove = (len(game_state.move_history) // 2) + 1

        fen = f"{piece_placement} {active_color} {castling} {ep_target} {halfmove} {fullmove}"
        return fen

    def _piece_to_fen_char(self, piece):
        """
        Convert piece object to FEN character.
        Uppercase = white, lowercase = black.
        """
        from chess_engine.pieces import (
            Pawn, Rook, Knight, Bishop, Queen, King
        )

        symbols = {
            Pawn:   'P',
            Knight: 'N',
            Bishop: 'B',
            Rook:   'R',
            Queen:  'Q',
            King:   'K',
        }

        char = symbols.get(type(piece), '?')

        # White pieces: uppercase (P, N, B, R, Q, K)
        # Black pieces: lowercase (p, n, b, r, q, k)
        return char if piece.color == 'white' else char.lower()

    def _get_castling_fen(self, game_state):
        """
        Generate castling rights string for FEN.

        K = white can castle kingside
        Q = white can castle queenside
        k = black can castle kingside
        q = black can castle queenside
        - = no castling available
        """
        from chess_engine.pieces import King, Rook

        castling = ''
        board    = game_state.board

        # White kingside: King on e1, Rook on h1, neither moved
        white_king = board.get_piece(7, 4)
        if (isinstance(white_king, King) and
                white_king.color == 'white' and
                not white_king.has_moved):
            white_rook_k = board.get_piece(7, 7)
            if (isinstance(white_rook_k, Rook) and
                    not white_rook_k.has_moved):
                castling += 'K'

        # White queenside: King on e1, Rook on a1
        white_rook_q = board.get_piece(7, 0)
        if (white_king and
                isinstance(white_king, King) and
                not white_king.has_moved):
            if (isinstance(white_rook_q, Rook) and
                    not white_rook_q.has_moved):
                castling += 'Q'

        # Black kingside: King on e8, Rook on h8
        black_king = board.get_piece(0, 4)
        if (isinstance(black_king, King) and
                black_king.color == 'black' and
                not black_king.has_moved):
            black_rook_k = board.get_piece(0, 7)
            if (isinstance(black_rook_k, Rook) and
                    not black_rook_k.has_moved):
                castling += 'k'

        # Black queenside: King on e8, Rook on a8
        black_rook_q = board.get_piece(0, 0)
        if (black_king and
                isinstance(black_king, King) and
                not black_king.has_moved):
            if (isinstance(black_rook_q, Rook) and
                    not black_rook_q.has_moved):
                castling += 'q'

        return castling if castling else '-'

    # ─────────────────────────────────────────────────
    # FALLBACK
    # ─────────────────────────────────────────────────

    def _random_move(self, game_state):
        """
        Fallback when Stockfish unavailable.
        Picks a random legal move.
        """
        import random

        all_legal = game_state.move_generator.get_all_legal_moves(
            game_state.current_turn
        )

        if not all_legal:
            return None

        # Pick random piece with legal moves
        from_pos = random.choice(list(all_legal.keys()))
        to_pos   = random.choice(all_legal[from_pos])

        from_sq = game_state.board.coords_to_notation(
            from_pos[0], from_pos[1]
        )
        to_sq = game_state.board.coords_to_notation(
            to_pos[0], to_pos[1]
        )

        return (from_sq, to_sq)

    def is_available(self):
        """Check if Stockfish is properly initialized."""
        return self._initialized