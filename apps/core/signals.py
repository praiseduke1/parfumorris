import os

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.sites.models import Site


@receiver(post_migrate)
def update_site_domain(sender, **kwargs):
    VERCEL_URL = os.getenv('VERCEL_URL')
    VERCEL_PROD = os.getenv('VERCEL_PROJECT_PRODUCTION_URL')
    domain = VERCEL_URL or VERCEL_PROD or 'localhost:8000'
    name = os.getenv('SITE_NAME', 'ParfuMoray')

    try:
        site = Site.objects.get_current()
        changed = False
        if site.domain != domain:
            site.domain = domain
            changed = True
        if site.name != name:
            site.name = name
            changed = True
        if changed:
            site.save()
    except Exception:
        pass
