from django.db import migrations


def update_default_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        id=1,
        defaults={'domain': 'localhost:8000', 'name': 'ParfuMoray'},
    )


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0010_add_label_choices'),
        ('sites', '__first__'),
    ]

    operations = [
        migrations.RunPython(update_default_site),
    ]
