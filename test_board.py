# test_board.py  (run this directly, not through Django)
from chess_engine.board import Board

b = Board()
b.display()

# Test coordinate conversion
print(Board.notation_to_coords('e2'))   # should print (6, 4)
print(Board.coords_to_notation(6, 4))  # should print 'e2'
print(Board.notation_to_coords('a8'))  # should print (0, 0)

# Test piece access
piece = b.get_piece(7, 4)
print(piece)                            # should print 'white King'

# Test a move
b.move_piece(6, 4, 4, 4)   # e2 → e4 (pawn opening move)
b.display()
from chess_engine.board import Board
from chess_engine.move_generator import MoveGenerator

print("=== Move Generation Tests ===\n")

b = Board()
mg = MoveGenerator(b)

# Test 1: Pawn opening moves
moves = mg.get_legal_moves(6, 4)  # e2 pawn
print(f"e2 pawn moves: {[b.coords_to_notation(r,c) for r,c in moves]}")
# Expected: ['e3', 'e4']

# Test 2: Knight opening moves
moves = mg.get_legal_moves(7, 1)  # b1 knight
print(f"b1 knight moves: {[b.coords_to_notation(r,c) for r,c in moves]}")
# Expected: ['a3', 'c3']

# Test 3: No moves for blocked pieces at start
moves = mg.get_legal_moves(7, 0)  # a1 rook (blocked)
print(f"a1 rook moves: {[b.coords_to_notation(r,c) for r,c in moves]}")
# Expected: []

# Test 4: Check detection
print(f"\nWhite in check at start: {mg.is_in_check('white')}")
# Expected: False

# Test 5: All white opening moves
all_moves = mg.get_all_legal_moves('white')
total = sum(len(v) for v in all_moves.values())
print(f"Total white legal moves at start: {total}")
# Expected: 20 (16 pawn + 4 knight moves)
# Fool's mate - fastest checkmate in chess (2 moves)
b2 = Board()
mg2 = MoveGenerator(b2)

# White plays f3
b2.move_piece(6, 5, 5, 5)
# Black plays e5
b2.move_piece(1, 4, 3, 4)
# White plays g4
b2.move_piece(6, 6, 4, 6)
# Black plays Qh4 - checkmate!
b2.move_piece(0, 3, 4, 7)

b2.display()
print(f"White in check: {mg2.is_in_check('white')}")
print(f"White checkmated: {mg2.is_checkmate('white')}")
# Both should be True
# Debug fool's mate
king_pos = b2.find_king('white')
print(f"White king at: {b2.coords_to_notation(king_pos[0], king_pos[1])}")

queen_pos = (4, 7)  # h4
queen_piece = b2.get_piece(4, 7)
print(f"Piece at h4: {queen_piece}")

# See what moves the black queen has
queen_moves = mg2._get_pseudo_legal_moves(4, 7, queen_piece)
print(f"Queen moves: {[b2.coords_to_notation(r,c) for r,c in queen_moves]}")