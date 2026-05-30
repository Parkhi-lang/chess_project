from django.db import models
import uuid

class Game(models.Model):
    STATUS_CHOICES = [(
        'active', 'Active'),
        ('checkmate','Checkmate'),
        ('stalemate','Stalemate'),
        ('timeout','Timeout'),
        ('resigned','Resigned'),
        ('draw','Draw')
        ]
    id = models.UUIDField(primary_key = True,
                          default = uuid.uuid4,
                          editable = False)
    status = models.CharField(max_length = 20, choices = STATUS_CHOICES,
                              default = 'active') 
    
    winner = models.CharField(max_length =10, null= True,blank = True )
    white_player = models.CharField(max_length =100,default = 'Player 1')
    black_player = models.CharField(max_length=100, default = 'Player 2')
    time_control = models.IntegerField(default =10)
    increment = models.IntegerField(default =0)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    game_state_data = models.JSONField(default = dict)
    class Meta :
        ordering = ['-created_at']
    def __str__(self):
        return f"Game{self.id}-{self.white_player} vs {self.black_player}"
class Move(models.Model):
    game = models.ForeignKey(Game, on_delete = models.CASCADE,
                             related_name = 'moves')    
    move_number = models.IntegerField()
    color = models.CharField(max_length = 10)
    piece = models.CharField(max_length = 20)
    from_square = models.CharField(max_length = 2)
    to_square = models.CharField(max_length = 2)
    captured = models.CharField(max_length = 20, null = True, blank = True)
    special = models.CharField(max_length = 20, null = True, blank = True)
    time_spent = models.FloatField(default = 0.0)
    timestemp = models.DateTimeField(auto_now_add = True)

    class Meta :
        ordering = ['move_number']
    def __str__(self):
        return f"Move{self.move_number}: {self.color}{self.piece}"     

    
# Create your models here.
