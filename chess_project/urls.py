# chess_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import FileResponse, HttpResponse
import os

def serve_frontend(request):
    """Serve the chess frontend HTML file through Django."""
    frontend_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'frontend', 'index.html'
    )
    with open(frontend_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='text/html')

def serve_js(request):
    """Serve board.js through Django."""
    js_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'frontend', 'board.js'
    )
    with open(js_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(),
                          content_type='application/javascript')

def serve_css(request):
    """Serve style.css through Django."""
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'frontend', 'style.css'
    )
    with open(css_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='text/css')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('board.js', serve_js,       name='serve-js'),
    path('style.css', serve_css,     name='serve-css'),
    path('',          serve_frontend, name='frontend'),
]