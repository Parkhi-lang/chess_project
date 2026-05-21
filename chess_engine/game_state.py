from chess_engine.board import Board
from chess_engine.move_generator import MoveGenerator
from chess_engine.pieces import Pawn, Rook, Knight, King,Queen,Bishop
class GameState:
    def __init__(self):
        self.board = Board()
        self.move_generator = MoveGenerator(self.board)
        self.current_turn = 'white'
        self.en_passant_target = None
        self.move_history = []
        self.status = 'active'
        self.winner = None
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
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        self._update_status()
        return {
            'success':True,
            'move':f"{from_notation}{to_notation}",
            'special': move_info.get('special'),
            'status': self.status,
            'check': self.move_generator.is_in_check(self.current_turn)

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
                    'move_count': len(self.move_history)

                }                                                          
      