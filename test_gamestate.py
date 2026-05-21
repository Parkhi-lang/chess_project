# test_gamestate.py
from chess_engine.game_state import GameState

gs = GameState()

# Test 1: Basic moves
print("=== Basic Move Test ===")
result = gs.make_move('e2', 'e4')
print(f"e2→e4: {result['success']}")  # True

result = gs.make_move('e7', 'e5')
print(f"e7→e5: {result['success']}")  # True

# Test 2: Wrong turn
print("\n=== Wrong Turn Test ===")
result = gs.make_move('d7', 'd5')     # Black just moved, white's turn
print(f"Black moves twice: {result}")  # success: False

# Test 3: Legal move highlights
print("\n=== Move Highlighting Test ===")
gs2 = GameState()
moves = gs2.get_legal_moves_for_square('e2')
print(f"e2 pawn can go to: {moves}")  # ['e3', 'e4']

moves = gs2.get_legal_moves_for_square('g1')
print(f"g1 knight can go to: {moves}")  # ['f3', 'h3']

# Test 4: Board state dict
print("\n=== Board State Test ===")
state = gs2.get_board_state()
print(f"Turn: {state['turn']}")        # white
print(f"Status: {state['status']}")   # active
print(f"Pieces on board: {len(state['board'])}")  # 32
# add to test_gamestate.py temporarily
gs3 = GameState()
state = gs3.get_board_state()
print(f"\nPieces found: {len(state['board'])}")
for p in state['board']:
    print(p)