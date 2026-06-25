from django.contrib import admin

from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical

admin.site.register(RadicalSession)
admin.site.register(RadicalSessionRadical)
