from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LanguageModelConfig(AppConfig):
    name = "neves_be.language_model"
    verbose_name = _("language model")
