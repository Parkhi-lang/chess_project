class Piece:
    '''Base class for chess pieces'''
    def __init__(self,color):
        self.color = color
        self.has_moved = False
    def opponent(self):
        '''Returns the color of the opponent'''
        return 'black' if self.color == 'white' else 'white'

    def __repr__(self):
        return f'{self.color}{self.__class__.__name__}'
        
class Pawn(Piece):
    symbol = 'P'

class Rook(Piece):
    symbol = 'R'
class Knight(Piece):
    symbol = 'N' 
class Bishop(Piece):
    symbol = "B"   
class Queen(Piece):
    symbol = "Q" 
class King(Piece):
    symbol = "K"                             