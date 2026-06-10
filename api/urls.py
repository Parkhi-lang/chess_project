# api/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('game/new/',
         views.NewGameView.as_view(),
         name='new-game'),

    path('game/<uuid:game_id>/',
         views.GameDetailView.as_view(),
         name='game-detail'),

    path('game/<uuid:game_id>/move/',
         views.MakeMoveView.as_view(),
         name='make-move'),

    path('game/<uuid:game_id>/moves/',
         views.LegalMovesView.as_view(),
         name='legal-moves'),

    path('game/<uuid:game_id>/resign/',
         views.ResignView.as_view(),
         name='resign'),

    path('game/<uuid:game_id>/review/',
         views.GameReviewView.as_view(),
         name='game-review'),
]