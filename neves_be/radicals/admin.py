from django.contrib import admin

from neves_be.radicals.models import Logogram
from neves_be.radicals.models import LogogramWordMap
from neves_be.radicals.models import Radical
from neves_be.radicals.models import RadicalLogogramMap
from neves_be.radicals.models import Sentence
from neves_be.radicals.models import Word
from neves_be.radicals.models import WordSentenceMap


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
