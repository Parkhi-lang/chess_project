from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Game, Move
from .serializers import (GameSerializer, NewGameSerializer,
                           MakeMoveSerializer)
from chess_engine.game_state import GameState


class NewGameView(APIView):
    """
    POST /api/game/new/
    Creates a new chess game and returns the game ID.
    """

    def post(self, request):
        serializer = NewGameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Create engine game state
        gs = GameState(
            minutes=data['time_control'],
            increment_seconds=data['increment']
        )

        # Save to database
        game = Game.objects.create(
            white_player=data['white_player'],
            black_player=data['black_player'],
            time_control=data['time_control'],
            increment=data['increment'],
            game_state_data=gs.to_dict()    # serialize engine state → DB
        )

        return Response({
            'game_id': str(game.id),
            'message': 'Game created successfully',
            'white_player': game.white_player,
            'black_player': game.black_player,
            'time_control': f"{game.time_control}+{game.increment}",
            'board': gs.get_board_state()
        }, status=status.HTTP_201_CREATED)


class GameDetailView(APIView):
    """
    GET /api/game/{id}/
    Returns current board state and game info.
    """

    def get(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)

        # Restore engine state from database
        gs = GameState.from_dict(game.game_state_data)

        return Response({
            'game_id': str(game.id),
            'status': game.status,
            'winner': game.winner,
            'white_player': game.white_player,
            'black_player': game.black_player,
            'board': gs.get_board_state(),
        })


class MakeMoveView(APIView):
    """
    POST /api/game/{id}/move/
    Makes a move and returns updated board state.
    """

    def post(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)

        # Can't move in a finished game
        if game.status != 'active':
            return Response(
                {'error': f'Game is already over. Result: {game.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate move input
        serializer = MakeMoveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Restore engine state from DB
        gs = GameState.from_dict(game.game_state_data)

        # Execute the move
        result = gs.make_move(
            data['from_square'],
            data['to_square'],
            data.get('promotion_piece', 'Q')
        )

        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save move to DB
        last_move = gs.move_history[-1]
        Move.objects.create(
            game=game,
            move_number=last_move['move_number'],
            color=last_move['color'],
            piece=last_move['piece'],
            from_square=last_move['from'],
            to_square=last_move['to'],
            captured=last_move.get('captured'),
            special=last_move.get('special'),
            time_spent=last_move.get('time_spent', 0.0)
        )

        # Update game status in DB
        game.status = result['status']
        game.winner = result.get('winner')
        game.game_state_data = gs.to_dict()   # save updated engine state
        game.save()

        return Response({
            'success': True,
            'move': result['move'],
            'special': result.get('special'),
            'status': result['status'],
            'check': result.get('check', False),
            'times': result.get('times'),
            'board': gs.get_board_state()
        })


class LegalMovesView(APIView):
    """
    GET /api/game/{id}/moves/?square=e2
    Returns all legal moves for a piece (used for highlighting).
    """

    def get(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)
        square = request.query_params.get('square')

        if not square:
            return Response(
                {'error': 'Provide a square parameter e.g. ?square=e2'},
                status=status.HTTP_400_BAD_REQUEST
            )

        gs = GameState.from_dict(game.game_state_data)
        moves = gs.get_legal_moves_for_square(square)

        return Response({
            'square': square,
            'legal_moves': moves
        })


class ResignView(APIView):
    """
    POST /api/game/{id}/resign/
    Body: {"color": "white"} or {"color": "black"}
    """

    def post(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)

        if game.status != 'active':
            return Response(
                {'error': 'Game is already over'},
                status=status.HTTP_400_BAD_REQUEST
            )

        color = request.data.get('color')
        if color not in ['white', 'black']:
            return Response(
                {'error': 'color must be white or black'},
                status=status.HTTP_400_BAD_REQUEST
            )

        game.status = 'resigned'
        game.winner = 'black' if color == 'white' else 'white'
        game.save()

        return Response({
            'message': f'{color} resigned',
            'winner': game.winner
        })

