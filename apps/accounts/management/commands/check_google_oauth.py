"""
Management command to diagnose Google OAuth configuration.

Usage:
    python manage.py check_google_oauth

Checks all configuration points and reports status.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.google.provider import GoogleProvider


class Command(BaseCommand):
    help = 'Check Google OAuth configuration and diagnose issues'

    def handle(self, *args, **options):
        self.check_count = 0
        self.pass_count = 0
        self.fail_count = 0

        self.stdout.write(self.style.MIGRATE_HEADING('Google OAuth Configuration Check'))
        self.stdout.write('=' * 60)

        self.check_env_loaded()
        self.check_env_vars()
        self.check_installed_apps()
        self.check_middleware()
        self.check_auth_backends()
        self.check_site_id()
        self.check_site_record()
        self.check_socialaccount_providers()
        self.check_app_config()
        self.check_socialapp_db()
        self.check_credential_resolution()

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Summary'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Checks:  {self.check_count}')
        self.stdout.write(f'  Passed:  {self.pass_count}')
        self.stdout.write(f'  Failed:  {self.fail_count}')

        if self.fail_count == 0:
            if self._has_real_creds:
                self.stdout.write('  Status:  OAuth Ready')
            else:
                self.stdout.write('  Status:  Configuration complete (credentials needed)')
        else:
            self.stdout.write('  Status:  Configuration errors detected')

    def msg(self, label, status, detail=''):
        icon = 'PASS' if status else 'FAIL'
        label = label.ljust(50)
        detail = f' -- {detail}' if detail else ''
        self.stdout.write(f'  [{icon}] {label}{detail}')
        self.check_count += 1
        if status:
            self.pass_count += 1
        else:
            self.fail_count += 1

    def check_env_loaded(self):
        self._has_real_creds = False
        dotenv_path = os.path.join(settings.BASE_DIR, '.env')
        status = os.path.exists(dotenv_path)
        self.msg('.env file exists', status,
                 f'found' if status else 'MISSING')

    def check_env_vars(self):
        cid = os.getenv('GOOGLE_CLIENT_ID', '').strip()
        csec = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()
        both_set = bool(cid) and bool(csec)
        self._has_real_creds = both_set
        self.msg('GOOGLE_CLIENT_ID loaded', bool(cid),
                 '(set)' if cid else '(EMPTY)')
        self.msg('GOOGLE_CLIENT_SECRET loaded', bool(csec),
                 '(set)' if csec else '(EMPTY)')

    def check_installed_apps(self):
        required = [
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
            'allauth.socialaccount.providers.google',
            'django.contrib.sites',
        ]
        for app in required:
            self.msg(f"INSTALLED_APPS contains '{app}'",
                     app in settings.INSTALLED_APPS)

    def check_middleware(self):
        has = any(
            'AccountMiddleware' in m
            for m in settings.MIDDLEWARE
        )
        self.msg("MIDDLEWARE has AccountMiddleware", has)

    def check_auth_backends(self):
        has = 'allauth.account.auth_backends.AuthenticationBackend' in settings.AUTHENTICATION_BACKENDS
        self.msg("AUTHENTICATION_BACKENDS has allauth backend", has)

    def check_site_id(self):
        self.msg('SITE_ID is set',
                 hasattr(settings, 'SITE_ID') and settings.SITE_ID is not None,
                 str(settings.SITE_ID))

    def check_site_record(self):
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            self.msg(f"Site id={settings.SITE_ID} exists in DB", True,
                     f"domain='{site.domain}' name='{site.name}'")
        except Site.DoesNotExist:
            self.msg(f"Site id={settings.SITE_ID} exists in DB", False,
                     'RECORD NOT FOUND')

    def check_socialaccount_providers(self):
        has = 'google' in settings.SOCIALACCOUNT_PROVIDERS
        self.msg("SOCIALACCOUNT_PROVIDERS has 'google'", has)
        if has:
            cfg = settings.SOCIALACCOUNT_PROVIDERS['google']
            self.msg("  scope includes email & profile",
                     set(cfg.get('SCOPE', [])) >= {'email', 'profile'})
            self.msg("  VERIFIED_EMAIL is True",
                     cfg.get('VERIFIED_EMAIL') is True)

    def check_app_config(self):
        cfg = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        app = cfg.get('APP')
        has_app = app is not None
        if self._has_real_creds:
            # When env vars are set, APP should be present with non-empty values
            ok = has_app and bool(app.get('client_id', '')) and bool(app.get('secret', ''))
            self.msg("APP config correctly injected from env vars", ok)
        else:
            # When env vars are empty, APP should be absent to allow DB fallback
            ok = not has_app
            self.msg("APP config absent (correct - allows DB fallback)", ok)
        if has_app:
            self.msg(f"  client_id='{app.get('client_id', '')}'",
                     bool(app.get('client_id', '')))
            self.msg(f"  secret='****'", bool(app.get('secret', '')))
        else:
            self.msg("  (allauth will use SocialApp DB record)", True)

    def check_socialapp_db(self):
        apps = SocialApp.objects.filter(provider='google')
        count = apps.count()
        status = count > 0
        self.msg(f"SocialApp(provider='google') in DB", status,
                 f'{count} record(s)' if status else 'NONE FOUND')
        if status:
            for app in apps:
                self.msg(f"  id={app.id} client_id='{app.client_id}'",
                         bool(app.client_id))
                sites = list(app.sites.values_list('domain', flat=True))
                self.msg(f"  assigned sites: {sites}", len(sites) > 0)
                self.msg(f"  name='{app.name}'", bool(app.name))
        else:
            if self._has_real_creds:
                self.msg("  (Env vars will be used after APP config fix)", True)
            else:
                self.msg("  >>> ACTION: Create at /admin/socialaccount/socialapp/", False,
                         'Or set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env')

    def check_credential_resolution(self):
        """Simulate what allauth does when building the OAuth URL."""
        has_any_creds = self._has_real_creds or SocialApp.objects.filter(provider='google').exists()
        if has_any_creds:
            self.msg("Allauth credential resolution test", True, '(credentials present)')
        else:
            self.msg("Allauth credential resolution test", True, '(no credentials - skip)')
            self.msg("  (Cannot resolve - configure credentials first)", True)
            return
        adapter = DefaultSocialAccountAdapter()
        try:
            from django.http import HttpRequest
            req = HttpRequest()
            req.META['SERVER_NAME'] = 'localhost'
            req.META['SERVER_PORT'] = '8000'
            req.META['HTTP_HOST'] = 'localhost:8000'
            provider = GoogleProvider(request=req)
            try:
                app = adapter.get_app(request=req, provider=provider)
                has_cid = bool(app.client_id)
                self.msg("  adapter.get_app() resolved client_id", has_cid,
                         f"client_id='{app.client_id}'" if has_cid else 'EMPTY')
            except Exception as e:
                self.msg("  adapter.get_app()", False, str(e))
        except Exception as e:
            self.msg("  provider instantiation", False, str(e))
