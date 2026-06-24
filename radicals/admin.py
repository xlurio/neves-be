from django.contrib import admin

from radicals.models import Logogram
from radicals.models import LogogramWordMap
from radicals.models import Radical
from radicals.models import RadicalLogogramMap
from radicals.models import RadicalSession
from radicals.models import RadicalSessionRadical
from radicals.models import RadicalSessionTest
from radicals.models import RadicalSessionTestQuestion
from radicals.models import Sentence
from radicals.models import Word
from radicals.models import WordSentenceMap


@admin.register(Radical)
class RadicalAdmin(admin.ModelAdmin):
    list_display = ["id", "pinyin", "meaning"]
    search_fields = ["id", "pinyin", "meaning"]


@admin.register(Logogram)
class LogogramAdmin(admin.ModelAdmin):
    list_display = ["id", "occurrences", "pinyin"]
    search_fields = ["id", "pinyin", "meaning"]


admin.site.register(RadicalLogogramMap)
admin.site.register(Word)
admin.site.register(LogogramWordMap)
admin.site.register(Sentence)
admin.site.register(WordSentenceMap)
admin.site.register(RadicalSession)
admin.site.register(RadicalSessionRadical)
admin.site.register(RadicalSessionTest)
admin.site.register(RadicalSessionTestQuestion)
