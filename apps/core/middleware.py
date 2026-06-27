from django.conf import settings


class DynamicCsrfTrustedOriginsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        origin = f'{scheme}://{host}'
        if origin not in settings.CSRF_TRUSTED_ORIGINS:
            settings.CSRF_TRUSTED_ORIGINS.append(origin)
        return self.get_response(request)


class SeparateAdminSessionMiddleware:
    ADMIN_COOKIE = 'admin_sessionid'
    USER_COOKIE = 'sessionid'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin_path = request.path.startswith('/admin/')

        if is_admin_path:
            self._prepare_admin_request(request)
            response = self.get_response(request)
            self._finalize_admin_response(request, response)
        else:
            response = self.get_response(request)

        return response

    def _prepare_admin_request(self, request):
        admin_sid = request.COOKIES.get(self.ADMIN_COOKIE)
        user_sid = request.COOKIES.get(self.USER_COOKIE)

        if admin_sid:
            request.COOKIES[self.USER_COOKIE] = admin_sid
            if user_sid is not None:
                request._frontend_sid = user_sid
        elif user_sid is not None:
            request._frontend_sid = user_sid
            del request.COOKIES[self.USER_COOKIE]

    def _finalize_admin_response(self, request, response):
        if self.USER_COOKIE in response.cookies:
            admin_cookie_val = response.cookies[self.USER_COOKIE].value
            response.cookies[self.ADMIN_COOKIE] = admin_cookie_val
            response.cookies[self.ADMIN_COOKIE]['path'] = '/'
            del response.cookies[self.USER_COOKIE]

        if hasattr(request, '_frontend_sid'):
            request.COOKIES[self.USER_COOKIE] = request._frontend_sid
