from django.contrib import admin

from neves_be.radical_tests.models import RadicalSessionTest
from neves_be.radical_tests.models import RadicalSessionTestQuestion

admin.site.register(RadicalSessionTest)
admin.site.register(RadicalSessionTestQuestion)
