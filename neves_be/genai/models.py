from django.db import models


class GeneratedSpeech(models.Model):
    id = models.BigIntegerField(primary_key=True)
    audio = models.FileField()

    def __str__(self) -> str:
        return f"generated speech {self.id}: {self.audio.path}"


class GeneratedTranslation(models.Model):
    id = models.BigIntegerField(primary_key=True)
    output = models.TextField()

    def __str__(self):
        return f"generated translation {self.id}: {self.output}"
