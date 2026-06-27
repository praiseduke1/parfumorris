from django.contrib import messages
from django.shortcuts import redirect
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        pass

    def authentication_error(
        self,
        request,
        provider_id,
        error=None,
        exception=None,
        extra_context=None,
    ):
        error_map = {
            'access_denied': 'Login Google dibatalkan. Silakan coba lagi.',
            'redirect_uri_mismatch': 'Konfigurasi redirect URI tidak cocok. Hubungi administrator.',
        }
        error_code = error if isinstance(error, str) else ''
        msg = error_map.get(error_code, 'Terjadi kesalahan saat login dengan Google. Silakan coba lagi.')

        messages.error(request, msg)
        raise ImmediateHttpResponse(redirect('accounts:login'))

    def get_app(self, request, provider, client_id=None):
        try:
            return super().get_app(request, provider, client_id)
        except Exception:
            raise ImmediateHttpResponse(redirect('accounts:login'))
