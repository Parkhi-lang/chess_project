# api/serializers.py

from rest_framework import serializers
from .models import Game, Move


class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = [
            'id', 'move_number', 'color', 'piece',
            'from_square', 'to_square', 'captured',
            'special', 'time_spent', 'timestamp'
        ]


class GameSerializer(serializers.ModelSerializer):
    moves = MoveSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = [
            'id', 'status', 'winner',
            'white_player', 'black_player',
            'time_control', 'increment',
            'created_at', 'updated_at', 'moves'
        ]


class NewGameSerializer(serializers.Serializer):
    white_player  = serializers.CharField(max_length=100, default='Player 1')
    black_player  = serializers.CharField(max_length=100, default='Player 2')
    time_control  = serializers.IntegerField(min_value=1, max_value=180, default=10)
    increment     = serializers.IntegerField(min_value=0, max_value=60, default=0)


class MakeMoveSerializer(serializers.Serializer):
    from_square      = serializers.CharField(min_length=2, max_length=2)
    to_square        = serializers.CharField(min_length=2, max_length=2)
    promotion_piece  = serializers.CharField(max_length=1, default='Q')

    def validate_from_square(self, value):
        if not (value[0] in 'abcdefgh' and value[1] in '12345678'):
            raise serializers.ValidationError(
                f"'{value}' is not a valid square. Use format like 'e2'."
            )
        return value.lower()

    def validate_to_square(self, value):
        if not (value[0] in 'abcdefgh' and value[1] in '12345678'):
            raise serializers.ValidationError(
                f"'{value}' is not a valid square. Use format like 'e4'."
            )
        return value.lower()