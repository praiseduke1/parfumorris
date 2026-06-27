import os
from django.db import migrations


def create_socialapp(apps, schema_editor):
    SocialApp = apps.get_model('socialaccount', 'SocialApp')
    Site = apps.get_model('sites', 'Site')

    client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()

    if not client_id or not client_secret:
        return

    try:
        site = Site.objects.get(id=1)
    except Site.DoesNotExist:
        return

    app, created = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'Google',
            'client_id': client_id,
            'secret': client_secret,
        },
    )
    if created or not app.sites.filter(id=site.id).exists():
        app.sites.add(site)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0011_configure_default_site'),
        ('socialaccount', '__first__'),
    ]

    operations = [
        migrations.RunPython(create_socialapp),
    ]
