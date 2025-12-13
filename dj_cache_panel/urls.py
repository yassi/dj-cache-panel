from django.urls import path
from . import views

app_name = "dj_cache_panel"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "<str:cache_name>/keys/",
        views.key_search,
        name="key_search",
    ),
    path(
        "<str:cache_name>/keys/<str:key>/",
        views.key_detail,
        name="key_detail",
    ),
]
