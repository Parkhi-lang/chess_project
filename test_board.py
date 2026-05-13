# test_board.py  (run this directly, not through Django)
from chess_project.chess_engine.board import Board

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