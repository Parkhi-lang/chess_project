# test_clock.py
import time
from chess_engine.clock import ChessClock
from chess_engine.game_state import GameState

print("=== Clock Unit Tests ===\n")

# Test 1: Basic clock
clock = ChessClock(minutes=1, increment_seconds=5)
print(f"White starts with: {clock.get_remaining('white')}s")   # 60.0
print(f"Black starts with: {clock.get_remaining('black')}s")   # 60.0

# Test 2: Clock ticking
clock.start('white')
time.sleep(0.5)    # simulate 0.5 seconds thinking
spent = clock.press('white')
print(f"\nWhite spent: {spent}s")                              # ~0.5
print(f"White remaining: {clock.get_remaining('white')}s")    # ~64.5 (60 - 0.5 + 5 increment)

# Test 3: Integrate with game
print("\n=== Clock in Game ===\n")
gs = GameState(minutes=5, increment_seconds=3)

result = gs.make_move('e2', 'e4')
print(f"After e2→e4: {result['times']}")

result = gs.make_move('e7', 'e5')
print(f"After e7→e5: {result['times']}")

state = gs.get_board_state()
print(f"\nClock in board state: {state['clock']}")

# Test 4: Move time history
print(f"\nWhite move times: {gs.clock.get_move_time_history('white')}")
print(f"White avg time: {gs.clock.get_average_move_time('white')}s")