from django.urls import path

from neves_be.users.views import authenticate_view
from neves_be.users.views import user_create_view

urlpatterns = [
    path("authenticate", authenticate_view, name="api-authenticate"),
    path("users", user_create_view, name="api-users-create"),
]
