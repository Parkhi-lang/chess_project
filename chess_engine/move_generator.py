from chess_engine.pieces import Pawn, Rook, Knight, Bishop, Queen, King
class MoveGenerator:
    def __init__(self, board):
           self.board = board
    def get_legal_moves(self,row,col):
          piece = self.board.get_piece(row,col)
          if piece is None:
                return []
          pseudo_moves = self._get_pseudo_legal_moves(row,col,piece)
          legal_moves =[]
          for (to_row, to_col) in pseudo_moves:
                if not self._move_leaves_king_in_check(row,col,to_row,to_col, piece.color):
                      legal_moves.append((to_row,to_col))
          return legal_moves
    def get_all_legal_moves(self,color):
          all_moves = {}
          for row in range(8):
                for col in range(8):
                      piece = self.board.get_piece(row,col)
                      if piece and piece.color == color:
                            moves = self.get_legal_moves(row,col)
                            if moves:
                                  all_moves[(row,col)] = moves
          return all_moves
    def _get_pseudo_legal_moves(self,row,col,piece):
          if isinstance(piece,Pawn):
                return self._pawn_moves(row,col,piece)
          elif isinstance(piece,Rook):
                return self._sliding_moves(row,col,piece,[(0,1),(0,-1),(1,0),(-1,0)])
          elif isinstance(piece,Bishop):
                return self._sliding_moves(row,col,piece,[(1,1),(1,-1),(-1,1),(-1,-1)])
          elif isinstance(piece,Queen):
                return self._sliding_moves(row,col,piece, [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,-1)])
          elif isinstance(piece,Knight):
                return self._knight_moves(row,col,piece)
          elif isinstance(piece,King):
                return self._king_moves(row,col,piece)
          return []
    def _sliding_moves(self,row,col,piece,directions):
          moves = []
          for (dr,dc) in directions:
                r,c  = row + dr, col + dc
                while self.board.is_in_bounds(r,c):
                      if self.board.is_empty(r,c):
                            moves.append((r,c))
                      elif self.board.is_enemy(r,c,piece.color):
                            moves.append((r,c) )
                            break
                      else:
                            break
                      r += dr
                      c += dc
          return moves
    def _knight_moves(self,row,col,piece):
          moves =[]
          offsets = [
                (-2,-1),(-2,+1),
                (+2,-1),(+2,+1),
                (-1,-2),(-1,+2),
                (+1,-2),(+1,+2),
          ]
          for (dr,dc) in offsets:
                r,c = row+dr, col +dc
                if self.board.is_in_bounds(r,c):
                      if not self.board.is_friendly(r,c,piece.color):
                            moves.append((r,c))
          return moves
    def _pawn_moves(self,row,col,piece):
        moves = []
        direction = -1 if piece.color == 'white' else 1
        start_row =6 if piece.color == 'white' else 1
        r = row+direction
        if self.board.is_in_bounds(r,col) and self.board.is_empty(r,col):
              moves.append((r,col))
              if row == start_row:
                    r2 = row +2 * direction
                    if self.board.is_empty(r2,col):
                          moves.append((r2,col))
        for dc in [-1,1]:
              r,c = row+direction ,col+dc
              if self.board.is_in_bounds(r,c) and self.board.is_enemy(r,c,piece.color) :
                    moves.append((r,c))
        return moves
    def _king_moves(self,row,col,piece):
          moves = []
          offsets = [
                (-1,-1),(-1,0),(-1,1),
                (0,-1),(0,1),
                (1,-1),(1,0),(1,1)
          ]            
          for (dr,dc) in offsets:
                r,c = row+dr, col+dc
                if self.board.is_in_bounds(r,c):
                      if not self.board.is_friendly(r,c,piece.color):
                            moves.append((r,c))
          return moves                      
        
                            

                
    def is_in_check(self,color):
          king_pos = self.board.find_king(color)
          if king_pos is None:
                return False
          return self._is_square_attacked(king_pos[0],king_pos[1],color)
    
    def _is_square_attacked(self, row, col,defending_color):
          enemy_color  = 'black' if defending_color == 'white' else 'white'
          for r in range(8):
            for c in range(8):
                  piece = self.board.get_piece(r,c)
                  if piece and piece.color == enemy_color:
                        enemy_moves  = self._get_pseudo_legal_moves(r,c, piece)
                        if (row,col) in enemy_moves:
                              return True
          return False
    def _move_leaves_king_in_check(self, from_row, from_col, to_row, to_col,color):
          moving_piece = self.board.grid[from_row][from_col]
          captured_piece = self.board.grid[to_row][to_col]
          self.board.grid[to_row][to_col]=moving_piece
          self.board.grid[from_row][from_col]=None
          in_check = self.is_in_check(color)
          self.board.grid[from_row][from_col]= moving_piece
          self.board.grid[to_row][to_col]=captured_piece
          return in_check
    def is_checkmate(self,color):
          if not self.is_in_check(color):
                return False
          return len(self.get_all_legal_moves(color))==0
    def is_stalemate(self,color):
          if self.is_in_check(color):
                return False
          return len(self.get_all_legal_moves(color))==0                                                

          
                 
                
                                              
                     
                                
