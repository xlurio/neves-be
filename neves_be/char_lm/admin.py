from django import forms
from django.contrib import admin

from neves_be.char_lm.models import Logogram
from neves_be.char_lm.models import Radical
from neves_be.char_lm.models import RadicalLogogramMap


class RadicalLogogramMapAdminForm(forms.ModelForm):
    logogram = forms.ModelChoiceField(
        label="Logogram",
        queryset=Logogram.objects.all(),
        widget=forms.TextInput,
    )
    radical = forms.ModelChoiceField(
        label="Radical",
        queryset=Radical.objects.all(),
        widget=forms.TextInput,
    )

    class Meta:
        model = RadicalLogogramMap
        fields = ("logogram", "radical")


@admin.register(RadicalLogogramMap)
class RadicalLogogramMapAdmin(admin.ModelAdmin):
    form = RadicalLogogramMapAdminForm


admin.site.register(Radical)
