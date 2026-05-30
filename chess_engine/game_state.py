from chess_engine.board import Board
from chess_engine.move_generator import MoveGenerator
from chess_engine.pieces import Pawn, Rook, Knight, King,Queen,Bishop
from chess_engine.clock import ChessClock
class GameState:
    def __init__(self,minutes=10,increment_seconds =0):
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.current_turn = 'white'
        self.en_passant_target = None
        self.move_history = []
        self.status = 'active'
        self.winner = None
        self.clock = ChessClock(minutes, increment_seconds)
        self.clock.start('white')

    def make_move(self,from_notation, to_notation,promotion_piece = 'Q'):
        from_row, from_col = self.board.notation_to_coords(from_notation)
        to_row, to_col = self.board.notation_to_coords(to_notation)
        piece = self.board.get_piece(from_row,from_col)
        if piece is None:
            return {'success': False, 'error':'No piece at that square'}
        if piece.color!= self.current_turn:
            return {'success': False, 'error':f"It is {self.current_turn}'s turn"}
        legal_moves = self.move_generator.get_legal_moves(from_row,from_col)
        castling_moves = self._get_castling_moves(from_row,from_col)
        en_passant_moves = self._get_en_passant_moves(from_row,from_col)
        all_legal = legal_moves + castling_moves +en_passant_moves

        if (to_row, to_col) not in all_legal:
            return {'success':False,'error':'Illegal move'}
        
        move_info = self._execute_move(
            from_row, from_col, to_row, to_col, promotion_piece
        )

        self.move_history.append({
            'color': self.current_turn,
            'from': from_notation,
            'to':to_notation,
            'piece': piece.__class__.__name__,
            'captured': move_info.get('captured'),
            'special': move_info.get('special'),
            'move_number': len(self.move_history)+1
        })
        self.clock.press(self.current_turn)
        time_spent = self.clock.press(self.current_turn)
        self.move_history[-1]['time_spent'] = time_spent
        self.current_turn = "black" if self.current_turn == 'white' else 'white'
        if self.clock.is_flagged(self.current_turn):
             self.status = 'timeout'
             self.winner = self.current_turn
             return{
                  'success':True,
                  'move': f"{from_notation}{to_notation}",
                  'special': move_info.get('special'),
                  'status': 'timeout',
                  'winner':self.winner,
                  'times': self.clock.get_both_times()
             }
        self.clock.start(self.current_turn)
        self._update_status()
        return{
             'success': True,
             'move': f"{from_notation}{to_notation}",
             'special': move_info.get('special'),
             'status': self.status,
             'check': self.move_generator.is_in_check(self.current_turn),
             'times': self.clock.get_both_times()
        }        
        
    def _get_castling_moves(self,row,col):
        piece = self.board.get_piece(row,col)
        if not isinstance(piece,King):
            return[]
        if piece.has_moved :
            return[]
        if self.move_generator.is_in_check(piece.color):
            return[]
        moves =[]
        back_rank = 7 if piece.color == 'white' else 0

        if self._can_castle_kingside(piece.color,back_rank):
            moves.append((back_rank,6)) 
        if self._can_castle_queenside(piece.color,back_rank):
            moves.append((back_rank,2))

        return moves
    
    def _can_castle_kingside(self, color, back_rank):
        rook = self.board.get_piece(back_rank,7)
        if not isinstance(rook,Rook) or rook.has_moved:
            return False
        if not (self.board.is_empty(back_rank,5) and 
              self.board.is_empty(back_rank,6)):
            return False
        if(self.move_generator._is_square_attacked(back_rank,5,color) or
           self.move_generator._is_square_attacked(back_rank,6,color)):
            return False
        return True
    
    def _can_castle_queenside(self, color, back_rank):
        rook = self.board.get_piece(back_rank,0)
        if not isinstance(rook,Rook) or rook.has_moved:
            return False
        if not(self.board.is_empty(back_rank,1) and 
               self.board.is_empty(back_rank,2) and
               self.board.is_empty(back_rank,3)):
            return False
        if (self.move_generator._is_square_attacked(back_rank,2,color) or
            self.move_generator._is_square_attacked(back_rank,3,color)):
            return False
        return True
    
    def _get_en_passant_moves(self,row,col):
        piece = self.board.get_piece(row,col)
        if not isinstance(piece, Pawn):
            return[]
        if self.en_passant_target is None:
            return[]
        ep_row, ep_col = self.en_passant_target

        direction =-1 if piece.color == 'white' else 1            
        if row+direction == ep_row and abs(col-ep_col)==1:
            return [(ep_row,ep_col)]
        return[]
    
    def _execute_move(self,from_row,from_col,to_row,to_col,promotion_piece):
        piece = self.board.get_piece(from_row,from_col)
        move_info = {}

        if isinstance(piece,King) and abs(to_col - from_col)==2:
            self._execute_castling(from_row, from_col, to_row, to_col)
            move_info['special'] = 'castling'
        elif (isinstance(piece,Pawn) and self.en_passant_target == (to_row,to_col)):
            captured = self.board.move_piece(from_row, from_col,to_row,to_col)
            direction =1 if piece.color == 'white' else -1
            self.board.grid[to_row + direction][to_col]=None
            move_info['special']='en_passant'
            move_info['captured'] = 'Pawn'     
        else:
            captured = self.board.move_piece(from_row, from_col,to_row,to_col)
            if captured:
                move_info['captured']= captured.__class__.__name__
        if isinstance(piece,Pawn) and abs(to_row- from_row)==2:
            direction = -1 if piece.color == 'white' else 1
            self.en_passant_target = (to_row + direction , to_col)
        else:
            self.en_passant_target = None
        if isinstance (piece,Pawn) and (to_row==0 or to_row==7):
                self._promote_pawn(to_row,to_col,piece.color,promotion_piece)
                move_info['special'] = 'promotion'
        return move_info
    
    def _execute_castling(self,from_row,from_col,to_row,to_col):
            self.board.move_piece(from_row,from_col,to_row,to_col)
            if to_col ==6:
                self.board.move_piece(to_row,7,to_row,5)
            else:
                self.board.move_piece(to_row,0,to_row,3)
    
    def _promote_pawn(self,row,col,color,promotion_piece):
            piece_map={
                'Q': Queen, 'R':Rook,
                'B':Bishop,'N':Knight
            }
            PieceClass = piece_map.get(promotion_piece.upper(),Queen)
            self.board.grid[row][col]= PieceClass(color)
    
    def _update_status(self):
            color = self.current_turn
            if self.move_generator.is_checkmate(color):
                self.status = 'checkmate'
                self.winner = 'white' if color == 'black' else 'black'
            elif self.move_generator.is_stalemate(color):
                self.status = 'stalemate'
            else:
                self.status = 'active'
    
    def get_legal_moves_for_square(self,notation):
            row,col = self.board.notation_to_coords(notation)
            piece = self.board.get_piece(row,col)
            if piece is None:
                return[]
            moves = self.move_generator.get_legal_moves(row,col)
            moves+= self._get_castling_moves(row,col)
            moves+= self._get_en_passant_moves(row,col)

            return [self.board.coords_to_notation(r,c) for r,c in moves]

    
    def get_board_state(self):
            board_data =[]
            for row in range(8):
                for col in range(8):
                    piece = self.board.get_piece(row,col)
                    if piece:
                        board_data.append({
                            'square': self.board.coords_to_notation(row,col),
                            'piece': piece.__class__.__name__,
                            'color': piece.color
                        })
            return {
                    'board': board_data,
                    'turn': self.current_turn,
                    'status': self.status,
                    'winner': self.winner,
                    'move_count': len(self.move_history),
                    'clock': self.clock.to_dict()

                }

    def to_dict(self):
         board_data = {}
         for row in range(8):
              for col in range(8):
                   piece = self.board.get_piece(row,col)
                   if piece:
                        square = self.board.coords_to_notation(row,col)
                        board_data[square]={
                             'type': piece.__class__.__name__,
                             'color': piece.color,
                             'has_moved': piece.has_moved
                        }
         return{
               'board': board_data,
               'current_turn':  self.current_turn,
               'en_passant_target': self.en_passant_target,
               'move_history': self.move_history,
               'status': self.status,
               'winner': self.winner,
               'clock': {
                    'time_remaining': self.clock.time_remaining,
                    'increment': self.clock.increment,
                    'time_per_move': self.clock.time_per_move,

               }
          }

    @classmethod
    def from_dict(cls,data):
         from chess_engine.pieces import Pawn, Rook, Knight,Bishop, Queen,King
         piece_map = {
              'Pawn': Pawn,
              'Rook': Rook,
              'Knight':Knight,
              'Bishop': Bishop,
              'Queen': Queen,
              'King': King
         }
         gs = cls.__new__(cls)
         gs.board = Board()
         gs.board.grid =[[None]*8 for _ in range(8)]
         for square, piece_data in data['board'].items():
            row, col = Board.notation_to_coords(square)
            PieceClass = piece_map[piece_data['type']]
            piece = PieceClass(piece_data['color'])
            piece.has_moved = piece_data['has_moved']
            gs.board.grid[row][col] = piece

         gs.move_generator = MoveGenerator(gs.board)
         gs.current_turn = data['current_turn']
         gs.en_passant_target = data['en_passant_target']
         if gs.en_passant_target:
              gs.en_passant_target = tuple(gs.en_passant_target)
         gs.move_history = data['move_history']
         gs.status = data['status']
         gs.winner = data['winner']

         clock_data = data['clock']
         gs.clock = ChessClock(
              minutes = clock_data['time_remaining']['white']/60,
              increment_seconds = clock_data['increment']

         )    
         gs.clock.time_remaining = clock_data['time_remaining']
         gs.clock.time_per_move = clock_data['time_per_move']
         gs.clock.start(gs.current_turn)

         return gs