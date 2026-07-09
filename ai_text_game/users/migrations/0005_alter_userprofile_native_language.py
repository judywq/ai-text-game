from django.db import migrations, models


def clear_null_native_languages(apps, schema_editor):
    UserProfile = apps.get_model("users", "UserProfile")
    UserProfile.objects.filter(native_language__isnull=True).update(native_language="")


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_userprofile_native_language"),
    ]

    operations = [
        migrations.RunPython(clear_null_native_languages, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userprofile",
            name="native_language",
            field=models.CharField(
                blank=True,
                choices=[
                    ("en", "English"),
                    ("fr", "French"),
                    ("ja", "Japanese"),
                    ("zh", "Chinese"),
                ],
                default="",
                help_text="Language used for word explanations and UI copy where relevant.",
                max_length=10,
                verbose_name="Native language",
            ),
        ),
    ]
