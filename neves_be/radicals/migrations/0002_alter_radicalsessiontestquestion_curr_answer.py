from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("radicals", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="radicalsessiontestquestion",
            name="curr_answer",
            field=models.CharField(
                blank=True,
                choices=[("a", "A"), ("b", "B"), ("c", "C"), ("d", "D"), ("e", "E")],
                default="",
                max_length=1,
            ),
        ),
    ]