import time
class ChessClock:
    def __init__(self, minutes =10,increment_seconds=0):
        total_seconds = minutes*60
        self.time_remaining ={
            'white':float(total_seconds),
            'black': float(total_seconds)
        }
        self.increment = increment_seconds
        self.active_color = None
        self.turn_start_time = None
        self.time_per_move = {
            'white':[],
            'black':[]
        }
        self.is_running = False
    def start(self,color):
        self.active_color = color
        self.turn_start_time = time.time()
        self.is_running = True
    def press(self,color):
        if not self.is_running or self.active_color!= color:
            return 0.0
        time_spend = time.time()-self.turn_start_time
        self.time_remaining[color]-= time_spend
        self.time_remaining[color]+= self.increment
        self.time_per_move[color].append(round(time_spend,2))
        self.is_running = False
        self.active_color = None
        self.turn_start_time = None
        return round(time_spend,2)

    def get_remaining(self,color):
        remaining = self.time_remaining[color]
        if self.is_running and self.active_color == color:
            elapsed = time.time()- self.turn_start_time
            remaining -= elapsed
        return max(0.0,round(remaining,2))

    def is_flagged(self,color):
        return self.get_remaining(color)<=0

    def get_both_times(self):
        return{
            'white': self.get_remaining('white'),
            'black': self.get_remaining('black')
        }
    
    def get_average_move_time(self,color):
        moves = self.time_per_move[color]
        if not moves:
            return 0.0
        return round(sum(moves)/len(moves),2)
    
    def get_move_time_history(self,color):
        return self.time_per_move[color]

    def get_longest_think(self,color):
        moves = self.time_per_move[color]
        if not moves:
            return 0.0
        return max(moves)
    def to_dict(self):
        return{
            'white_remaining': self.get_remaining('white'),
            'black_remaining': self.get_remaining('black'),
            'active_color': self.active_color,
            'increment': self.increment,
            'white_move_times': self.time_per_move['white'], 
            'black_move_times': self.time_per_move['black']

        }
     