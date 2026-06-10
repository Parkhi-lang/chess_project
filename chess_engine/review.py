# chess_engine/review.py


class ReviewEngine:
    """
    Analyses a completed game and produces statistics.
    Takes move_history from GameState and produces insights.

    Usage:
        review = ReviewEngine(move_history, clock)
        summary = review.get_full_review()
    """

    # Standard piece values used in chess
    PIECE_VALUES = {
        'Pawn':   1,
        'Knight': 3,
        'Bishop': 3,
        'Rook':   5,
        'Queen':  9,
        'King':   0   # not counted in material
    }

    def __init__(self, move_history, clock=None):
        self.move_history = move_history   # list of move dicts from GameState
        self.clock = clock                 # ChessClock object (optional)

    # ─────────────────────────────────────────────────
    # GAME SUMMARY
    # ─────────────────────────────────────────────────

    def get_full_review(self):
        """
        Master method — returns complete game analysis.
        This is what the API endpoint will return.
        """
        return {
            'total_moves':        self.get_total_moves(),
            'moves_by_color':     self.get_moves_by_color(),
            'game_phases':        self.get_game_phases(),
            'captures':           self.get_capture_summary(),
            'material_timeline':  self.get_material_timeline(),
            'clock_analysis':     self.get_clock_analysis(),
            'longest_think':      self.get_longest_think(),
            'fastest_move':       self.get_fastest_move(),
            'opening_moves':      self.get_opening_moves(),
            'game_narrative':     self.get_game_narrative(),
        }

    # ─────────────────────────────────────────────────
    # BASIC STATS
    # ─────────────────────────────────────────────────

    def get_total_moves(self):
        """Total number of half-moves (plies) in the game."""
        return len(self.move_history)

    def get_moves_by_color(self):
        """How many moves each color made."""
        white = sum(1 for m in self.move_history if m['color'] == 'white')
        black = sum(1 for m in self.move_history if m['color'] == 'black')
        return {'white': white, 'black': black}

    def get_opening_moves(self, n=10):
        """
        Returns first N moves of the game.
        Useful for identifying opening patterns.
        """
        opening = self.move_history[:n]
        return [
            {
                'move_number': m['move_number'],
                'color':       m['color'],
                'piece':       m['piece'],
                'from':        m['from'],
                'to':          m['to'],
            }
            for m in opening
        ]

    # ─────────────────────────────────────────────────
    # GAME PHASES
    # ─────────────────────────────────────────────────

    def get_game_phases(self):
        """
        Divides game into opening, middlegame, endgame.

        Opening:     moves 1-10
        Middlegame:  moves 11-30
        Endgame:     moves 31+

        These are approximate — real engines use
        material count to determine phase.
        """
        total = len(self.move_history)

        opening_end    = min(10, total)
        middlegame_end = min(30, total)

        return {
            'opening': {
                'moves': self.move_history[:opening_end],
                'length': opening_end
            },
            'middlegame': {
                'moves': self.move_history[opening_end:middlegame_end],
                'length': max(0, middlegame_end - opening_end)
            },
            'endgame': {
                'moves': self.move_history[middlegame_end:],
                'length': max(0, total - middlegame_end)
            }
        }

    # ─────────────────────────────────────────────────
    # CAPTURES & MATERIAL
    # ─────────────────────────────────────────────────

    def get_capture_summary(self):
        """
        Summarizes all captures made in the game.
        Returns captures grouped by color.
        """
        captures = {'white': [], 'black': []}

        for move in self.move_history:
            if move.get('captured'):
                captures[move['color']].append({
                    'move_number':  move['move_number'],
                    'captured':     move['captured'],
                    'value':        self.PIECE_VALUES.get(move['captured'], 0),
                    'by_piece':     move['piece'],
                    'at_square':    move['to'],
                })

        # Add totals
        captures['white_material_gained'] = sum(
            c['value'] for c in captures['white']
        )
        captures['black_material_gained'] = sum(
            c['value'] for c in captures['black']
        )
        captures['material_advantage'] = (
            captures['white_material_gained'] -
            captures['black_material_gained']
        )

        return captures

    def get_material_timeline(self):
        """
        Tracks material balance after every capture.
        Returns list of {move, white_material, black_material, balance}

        balance > 0 means white is ahead
        balance < 0 means black is ahead
        """
        timeline = []
        white_lost = 0   # material white has lost (captured by black)
        black_lost = 0   # material black has lost (captured by white)

        # Starting material for each side
        # 8 pawns + 2 knights + 2 bishops + 2 rooks + 1 queen = 39
        STARTING_MATERIAL = 39

        for move in self.move_history:
            if move.get('captured'):
                value = self.PIECE_VALUES.get(move['captured'], 0)

                if move['color'] == 'white':
                    black_lost += value    # white captured black's piece
                else:
                    white_lost += value    # black captured white's piece

                timeline.append({
                    'move_number':      move['move_number'],
                    'color':            move['color'],
                    'captured_piece':   move['captured'],
                    'white_remaining':  STARTING_MATERIAL - white_lost,
                    'black_remaining':  STARTING_MATERIAL - black_lost,
                    'balance':          black_lost - white_lost,
                    # positive = white ahead, negative = black ahead
                })

        return timeline

    # ─────────────────────────────────────────────────
    # CLOCK ANALYSIS
    # ─────────────────────────────────────────────────

    def get_clock_analysis(self):
        """
        Analyses time usage for both players.
        Uses time_spent stored in each move.
        """
        white_times = [
            m.get('time_spent', 0)
            for m in self.move_history
            if m['color'] == 'white'
        ]
        black_times = [
            m.get('time_spent', 0)
            for m in self.move_history
            if m['color'] == 'black'
        ]

        def analyze(times):
            if not times:
                return {}
            return {
                'total_time_spent':   round(sum(times), 2),
                'average_per_move':   round(sum(times) / len(times), 2),
                'longest_think':      round(max(times), 2),
                'fastest_move':       round(min(times), 2),
                'move_times':         [round(t, 2) for t in times],
            }

        analysis = {
            'white': analyze(white_times),
            'black': analyze(black_times),
        }

        # Add clock remaining if clock object available
        if self.clock:
            analysis['white']['remaining'] = self.clock.get_remaining('white')
            analysis['black']['remaining'] = self.clock.get_remaining('black')

        return analysis

    def get_longest_think(self):
        """Which move had the longest think time overall."""
        if not self.move_history:
            return None

        moves_with_time = [
            m for m in self.move_history
            if m.get('time_spent', 0) > 0
        ]

        if not moves_with_time:
            return None

        slowest = max(moves_with_time, key=lambda m: m.get('time_spent', 0))
        return {
            'move_number': slowest['move_number'],
            'color':       slowest['color'],
            'move':        f"{slowest['from']}→{slowest['to']}",
            'time_spent':  slowest.get('time_spent', 0)
        }

    def get_fastest_move(self):
        """Which move was played fastest."""
        if not self.move_history:
            return None

        moves_with_time = [
            m for m in self.move_history
            if m.get('time_spent', 0) > 0
        ]

        if not moves_with_time:
            return None

        fastest = min(moves_with_time, key=lambda m: m.get('time_spent', 0))
        return {
            'move_number': fastest['move_number'],
            'color':       fastest['color'],
            'move':        f"{fastest['from']}→{fastest['to']}",
            'time_spent':  fastest.get('time_spent', 0)
        }

    # ─────────────────────────────────────────────────
    # SPECIAL MOVES SUMMARY
    # ─────────────────────────────────────────────────

    def get_special_moves(self):
        """Count of castling, en passant, promotions."""
        specials = {
            'castling':    [],
            'en_passant':  [],
            'promotion':   [],
        }

        for move in self.move_history:
            special = move.get('special')
            if special == 'castling':
                specials['castling'].append(move)
            elif special == 'en_passant':
                specials['en_passant'].append(move)
            elif special == 'promotion':
                specials['promotion'].append(move)

        return {
            'castling_count':   len(specials['castling']),
            'en_passant_count': len(specials['en_passant']),
            'promotion_count':  len(specials['promotion']),
            'details':          specials
        }

    # ─────────────────────────────────────────────────
    # GAME NARRATIVE
    # ─────────────────────────────────────────────────

    def get_game_narrative(self):
        """
        Generates a human-readable text summary of the game.
        Great for displaying to users after the game ends.
        """
        total = self.get_total_moves()
        captures = self.get_capture_summary()
        phases = self.get_game_phases()

        # Determine game length description
        if total < 20:
            length_desc = "a very short game"
        elif total < 40:
            length_desc = "a quick game"
        elif total < 60:
            length_desc = "a medium-length game"
        else:
            length_desc = "a long, hard-fought game"

        # Material advantage description
        balance = captures['material_advantage']
        if balance > 5:
            material_desc = "White dominated materially"
        elif balance > 0:
            material_desc = "White had a slight material edge"
        elif balance == 0:
            material_desc = "Material was equal throughout"
        elif balance > -5:
            material_desc = "Black had a slight material edge"
        else:
            material_desc = "Black dominated materially"

        # Game phase description
        endgame_len = phases['endgame']['length']
        if endgame_len > 20:
            phase_desc = "with a long endgame"
        elif endgame_len > 0:
            phase_desc = "reaching an endgame"
        else:
            phase_desc = "decided in the middlegame"

        narrative = (
            f"This was {length_desc} lasting {total} moves, "
            f"{phase_desc}. {material_desc}. "
            f"White captured {captures['white_material_gained']} points "
            f"of material while Black captured "
            f"{captures['black_material_gained']} points."
        )

        return narrative