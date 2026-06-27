import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class Command(BaseCommand):
    help = 'Check Google OAuth login configuration and diagnose issues'

    def handle(self, *args, **options):
        self.pass_count = 0
        self.fail_count = 0

        self.stdout.write(self.style.MIGRATE_HEADING('Google Login Configuration Check'))
        self.stdout.write('=' * 60)

        self.run_check('Dotenv loaded', self._check_dotenv)
        self.run_check('GOOGLE_CLIENT_ID loaded', self._check_env_var, 'GOOGLE_CLIENT_ID')
        self.run_check('GOOGLE_CLIENT_SECRET loaded', self._check_env_var, 'GOOGLE_CLIENT_SECRET')
        self.run_check('SOCIALACCOUNT_PROVIDERS has google', self._check_providers)
        self.run_check('SocialApp in database', self._check_socialapp_db)
        self.run_check('Site record exists', self._check_site)
        self.run_check('allauth URLs accessible', self._check_urls)
        self.run_check('OAuth callback configured', self._check_callback)
        self.run_check('Credential resolution test', self._check_resolution)

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Summary'))
        self.stdout.write('=' * 60)
        total = self.pass_count + self.fail_count
        self.stdout.write(f'  Checks:  {total}')
        self.stdout.write(f'  Passed:  {self.pass_count}')
        self.stdout.write(f'  Failed:  {self.fail_count}')

        if self.fail_count == 0:
            if self._has_real_creds() and self._has_socialapp_db():
                self.stdout.write(self.style.SUCCESS('  Status:  Google Login READY'))
            else:
                self.stdout.write(self.style.WARNING('  Status:  Configuration complete but missing credentials'))
        else:
            self.stdout.write(self.style.ERROR('  Status:  Configuration errors detected'))

        if self.fail_count == 0:
            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING('Test the Login'))
            self.stdout.write('=' * 60)
            self.stdout.write('  1. Run: python manage.py runserver')
            self.stdout.write('  2. Open: http://localhost:8000/accounts/login/')
            self.stdout.write('  3. Click "Lanjutkan dengan Google"')
            self.stdout.write('  4. You should see Google account chooser')
            self.stdout.write('  5. After login, you will be redirected to Dashboard')

    def msg(self, label, status, detail=''):
        icon = 'PASS' if status else 'FAIL'
        label = label.ljust(52)
        detail = f' -- {detail}' if detail else ''
        self.stdout.write(f'  [{icon}] {label}{detail}')

    def run_check(self, label, fn, *args):
        try:
            status, detail = fn(*args)
            self.msg(label, status, detail)
            if status:
                self.pass_count += 1
            else:
                self.fail_count += 1
        except Exception as e:
            self.msg(label, False, str(e))
            self.fail_count += 1

    def _has_real_creds(self):
        cid = os.getenv('GOOGLE_CLIENT_ID', '').strip()
        csec = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()
        return bool(cid) and bool(csec)

    def _has_socialapp_db(self):
        return SocialApp.objects.filter(provider='google').exists()

    def _check_dotenv(self):
        dotenv_path = os.path.join(settings.BASE_DIR, '.env')
        exists = os.path.exists(dotenv_path)
        return (exists, 'found' if exists else 'MISSING')

    def _check_env_var(self, name):
        val = os.getenv(name, '').strip()
        return (bool(val), f"'{val[:40]}...'" if bool(val) else '(EMPTY)')

    def _check_providers(self):
        has = 'google' in settings.SOCIALACCOUNT_PROVIDERS
        return (has, '')

    def _check_socialapp_db(self):
        apps = SocialApp.objects.filter(provider='google')
        count = apps.count()
        if count == 0:
            return (False, 'No SocialApp found — run migrate to auto-create')
        app = apps.first()
        cid_ok = bool(app.client_id)
        sites_ok = app.sites.count() > 0
        return (cid_ok and sites_ok,
                f"client_id='{app.client_id[:40]}...' sites={list(app.sites.values_list('domain', flat=True))}")

    def _check_site(self):
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            return (True, f"domain='{site.domain}' name='{site.name}'")
        except Site.DoesNotExist:
            return (False, f"Site id={settings.SITE_ID} not found")

    def _check_urls(self):
        try:
            from django.urls import resolve, Resolver404
            from django.http import HttpRequest
            req = HttpRequest()
            req.META['SERVER_NAME'] = 'localhost'
            req.META['SERVER_PORT'] = '8000'
            req.META['HTTP_HOST'] = 'localhost:8000'
            req.path = '/accounts/google/login/'
            resolve('/accounts/google/login/')
            resolve('/accounts/google/login/callback/')
            return (True, '/accounts/google/login/ and /callback/ resolved')
        except Resolver404 as e:
            return (False, str(e))

    def _check_callback(self):
        cid = os.getenv('GOOGLE_CLIENT_ID', '').strip()
        if not cid:
            return (True, 'Skipped (no client_id)')
        expected_redirect_uri = 'http://localhost:8000/accounts/google/login/callback/'
        return (True, f"Expected: {expected_redirect_uri}")

    def _check_resolution(self):
        has_any = self._has_real_creds() or self._has_socialapp_db()
        if not has_any:
            return (True, 'Skipped — no credentials to test')
        adapter = DefaultSocialAccountAdapter()
        try:
            from django.http import HttpRequest
            req = HttpRequest()
            req.META['SERVER_NAME'] = 'localhost'
            req.META['SERVER_PORT'] = '8000'
            req.META['HTTP_HOST'] = 'localhost:8000'
            app = adapter.get_app(request=req, provider='google', client_id=None)
            has_cid = bool(app.client_id)
            return (has_cid, f"client_id='{app.client_id[:40]}...'" if has_cid else 'EMPTY client_id')
        except Exception as e:
            return (False, str(e))
