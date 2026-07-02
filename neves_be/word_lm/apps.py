from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WordLmConfig(AppConfig):
    name = "neves_be.word_lm"
    verbose_name = _("language model")
