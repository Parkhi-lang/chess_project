from chess_project.chess_engine.pieces import Piece, Pawn, Rook, Knight,Bishop,Queen,King
class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.setup_pieces()

    def setup_pieces(self):
        self._place_back_rank('black',row=0)
        self._place_pawns('black',row =1)
        self._place_pawns('white',row=6)
        self._place_back_rank('white',row=7)

    def _place_back_rank(self,color,row):
        order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, PieceClass in enumerate(order):
            self.grid[row][col] = PieceClass(color)

    def _place_pawns(self,color,row):
        for col in range(8):
            self.grid[row][col]= Pawn(color)

    @staticmethod
    def notation_to_coords(notation):
        col = ord(notation[0]) -ord('a')
        row = 8- int(notation[1])
        return (row,col)
    @staticmethod
    def coords_to_notation(row,col):
        letter = chr(col + ord('a'))
        number = 8-row
        return f"{letter}{number}"
    def get_piece(self,row,col):
        return self.grid[row][col]
    def is_empty(self,row,col):
        return self.grid[row][col] is None
    def is_in_bounds(self,row,col):
        return 0<= row<=7  and 0<= col<=7
    def is_enenmy(self,row,col,color):
        piece = self.grid[row][col]
        return piece is not None and piece.color!=color
    def  is_friendly(self,row,col,color):
        piece = self.grid[row][col]
        return piece is not None and piece.color==color
    

    '''Movve execution
    '''
    def move_piece(self,from_row,from_col,to_row,to_col):
        piece = self.grid[from_row][from_col]
        captured = self.grid[to_row][to_col]

        self.grid[to_row][to_col] = piece
        self.grid[from_row][from_col] = None
        if piece:
            piece.has_moved = True
        return captured

    #debu display
    def display(self):
        print(" a b c d e f g h")
        print(" ---------------")
        for row in range(8):
            rank = 8-row
            line = f"{rank}| "
            for col in range(8):
                piece = self.grid[row][col]
                if piece is None:
                    line +=". "
                else:
                    symbol = piece.symbol
                    line +=(symbol.upper() if piece.color == 'white'
                                else symbol.lower()) + " " 
            print(line)
        print()               
                
        def find_king(self,color):
            for row in range(8):
                for col in range(8):
                    piece = self.grid[row][col]
                    if piece is not None and  piece.symbol == 'K' and piece.color == color:
                        return (row,col)
            