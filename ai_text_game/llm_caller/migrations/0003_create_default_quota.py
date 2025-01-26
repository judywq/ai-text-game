from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('llm_caller', '0002_apirequest_error'),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
