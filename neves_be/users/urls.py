from django.urls import path

from .views import authenticate_view
from .views import user_create_view
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view

app_name = "users"
web_urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]

api_urlpatterns = [
    path("authenticate", authenticate_view, name="api-authenticate"),
    path("users", user_create_view, name="api-users-create"),
]

urlpatterns = web_urlpatterns
