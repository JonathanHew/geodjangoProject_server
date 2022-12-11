from django.urls import path
from cafes.views import NearbyCafesView, QueryOverpass

urlpatterns = [
    # [...]
    path('nearbyCafes', NearbyCafesView.as_view()),
    path('osm-query', QueryOverpass.as_view()),
]