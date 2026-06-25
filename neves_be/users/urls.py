from django.urls import path

from .views import authenticate_view
from .views import user_create_view

app_name = "users"
urlpatterns = [
    path("authenticate", authenticate_view, name="api-authenticate"),
    path("users", user_create_view, name="api-users-create"),
]
