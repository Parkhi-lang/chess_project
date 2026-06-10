# test_review.py
from chess_engine.game_state import GameState
from chess_engine.review import ReviewEngine

print("=== Match Review Tests ===\n")

# Play a short game
gs = GameState(minutes=5, increment_seconds=0)

# Simulate a game with some captures
moves = [
    ('e2', 'e4'), ('e7', 'e5'),
    ('d2', 'd4'), ('e5', 'd4'),   # black captures white pawn
    ('d1', 'd4'), ('d7', 'd6'),   # white queen recaptures
    ('g1', 'f3'), ('g8', 'f6'),
    ('f1', 'c4'), ('f8', 'e7'),
    ('e1', 'g1'), ('e8', 'g8'),   # both castle
]

for from_sq, to_sq in moves:
    result = gs.make_move(from_sq, to_sq)
    if not result['success']:
        print(f"Move failed: {from_sq}→{to_sq}: {result['error']}")

print(f"Moves played: {len(gs.move_history)}")

# Run review
review = ReviewEngine(gs.move_history, gs.clock)

print(f"\n--- Basic Stats ---")
print(f"Total moves: {review.get_total_moves()}")
print(f"Moves by color: {review.get_moves_by_color()}")

print(f"\n--- Captures ---")
captures = review.get_capture_summary()
print(f"White captured: {captures['white_material_gained']} points")
print(f"Black captured: {captures['black_material_gained']} points")
print(f"Material advantage: {captures['material_advantage']}")

print(f"\n--- Material Timeline ---")
timeline = review.get_material_timeline()
for entry in timeline:
    print(f"Move {entry['move_number']}: "
          f"{entry['color']} captured {entry['captured_piece']} | "
          f"Balance: {entry['balance']}")

print(f"\n--- Clock Analysis ---")
clock_data = review.get_clock_analysis()
print(f"White avg time per move: {clock_data['white'].get('average_per_move')}s")
print(f"Black avg time per move: {clock_data['black'].get('average_per_move')}s")

print(f"\n--- Game Phases ---")
phases = review.get_game_phases()
print(f"Opening: {phases['opening']['length']} moves")
print(f"Middlegame: {phases['middlegame']['length']} moves")
print(f"Endgame: {phases['endgame']['length']} moves")

print(f"\n--- Special Moves ---")
specials = review.get_special_moves()
print(f"Castling: {specials['castling_count']}")
print(f"En passant: {specials['en_passant_count']}")
print(f"Promotions: {specials['promotion_count']}")

print(f"\n--- Game Narrative ---")
print(review.get_game_narrative())

print(f"\n--- Opening Moves ---")
for move in review.get_opening_moves(6):
    print(f"  {move['move_number']}. {move['color']} "
          f"{move['piece']} {move['from']}→{move['to']}")