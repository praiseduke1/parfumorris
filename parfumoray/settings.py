from pathlib import Path
from dotenv import load_dotenv
import os
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-vercel-temp-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').strip().lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = ['*']

csrf_origins_str = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins_str.split(',') if origin.strip()]

# Automatically add Vercel domains to trusted origins
if os.getenv('VERCEL_URL'):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.getenv('VERCEL_URL')}")
if os.getenv('VERCEL_PROJECT_PRODUCTION_URL'):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.getenv('VERCEL_PROJECT_PRODUCTION_URL')}")
CSRF_TRUSTED_ORIGINS.append("https://*.vercel.app")

DJANGO_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'django_cleanup.apps.CleanupConfig',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'storages',
]

LOCAL_APPS = [
    'apps.core',
    'apps.regions',
    'apps.accounts',
    'apps.products',
    'apps.carts',
    'apps.orders',
    'apps.payments',
    'apps.promotions',
    'apps.shipping',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'apps.core.middleware.SeparateAdminSessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'parfumoray.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'apps.core.context_processors.cart_count',
                'apps.core.context_processors.wishlist_ids',
                'apps.core.context_processors.voucher_notification',
                'apps.core.context_processors.voucher_floating_panel',
            ],
        },
    },
]

WSGI_APPLICATION = 'parfumoray.wsgi.application'

# Deteksi lingkungan Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1'

DATABASE_URL = os.environ.get('DATABASE_URL')

if IS_VERCEL:
    if DATABASE_URL:
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=300,
                ssl_require=True
            )
        }
    else:
        import sys
        print("WARNING: Vercel environment detected but DATABASE_URL is not set. Falling back to dummy PostgreSQL config.", file=sys.stderr)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': '',
                'USER': '',
                'PASSWORD': '',
                'HOST': '',
                'PORT': '',
            }
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'VERIFIED_EMAIL': True,
    }
}

ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*', 'username*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_ADAPTER = 'apps.accounts.adapter.CustomSocialAccountAdapter'

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https' if not DEBUG else 'http'

LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# Redis Cache (optional, falls back to locmem)
if os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PARSER_CLASS': 'redis.connection.HiredisParser',
            },
            'KEY_PREFIX': 'parfumoray',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'parfumoray-cache',
            'KEY_PREFIX': 'parfumoray',
        }
    }

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'parfumoray'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

JAZZMIN_SETTINGS = {
    "site_title": "Morris Parfum Admin",
    "site_header": "Morris Parfum",
    "site_brand": "Morris Parfum",
    "welcome_sign": "Selamat Datang di Dashboard Morris Parfum",
    "copyright": "Morris Parfum",
    "search_model": ["auth.User", "products.Product", "orders.Order"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Analytics", "url": "admin_dashboard", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
    ],
    "usermenu_links": [],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["products", "orders", "payments", "accounts", "auth", "promotions", "carts", "regions"],
    "custom_links": {},
    "icons": {
        "products.Product": "fas fa-box",
        "products.Category": "fas fa-tag",
        "products.Brand": "fas fa-certificate",
        "products.FragranceNote": "fas fa-leaf",
        "products.FragranceFamily": "fas fa-seedling",
        "products.ProductVariant": "fas fa-flask",
        "products.ProductImage": "fas fa-image",
        "products.ProductSlugRedirect": "fas fa-link",
        "products.Review": "fas fa-star",
        "orders.Order": "fas fa-cart-shopping",
        "orders.OrderItem": "fas fa-shopping-bag",
        "orders.OrderStatusHistory": "fas fa-clock-rotate-left",
        "orders.Voucher": "fas fa-ticket",
        "payments.Payment": "fas fa-credit-card",
        "payments.PaymentStatusHistory": "fas fa-clock-rotate-left",
        "auth.User": "fas fa-users",
        "auth.Group": "fas fa-users-cog",
        "promotions.Voucher": "fas fa-ticket",
        "promotions.UserVoucher": "fas fa-ticket-alt",
        "regions.City": "fas fa-location-dot",
        "regions.Province": "fas fa-map",
        "regions.District": "fas fa-location-dot",
        "regions.PostalCode": "fas fa-mailbox",
        "accounts.Profile": "fas fa-id-card",
        "accounts.CustomerAddress": "fas fa-location-dot",
        "accounts.Wishlist": "fas fa-heart",
        "accounts.MemberProfile": "fas fa-crown",
        "accounts.PointTransaction": "fas fa-coins",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.User": "collapsible",
        "orders.Order": "carousel",
    },
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Production media storage (Supabase Storage / S3-compatible).
# On Vercel serverless, local filesystem is ephemeral.
# Set AWS_ACCESS_KEY_ID + friends in Vercel env to persist uploads.
if os.getenv('AWS_ACCESS_KEY_ID'):
    STORAGES['default']['BACKEND'] = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', 'https://<project>.supabase.co/storage/v1/s3')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'ap-southeast-1')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'products:list'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400

BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
email_port_str = os.getenv('EMAIL_PORT', '587')
if email_port_str and email_port_str.strip():
    try:
        EMAIL_PORT = int(email_port_str)
    except ValueError:
        EMAIL_PORT = 587
else:
    EMAIL_PORT = 587
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').strip().lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

EMAIL_FILE_PATH = os.getenv('EMAIL_FILE_PATH', BASE_DIR / 'emails')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@parfumoray.com')

MIDTRANS_MERCHANT_ID = os.getenv('MIDTRANS_MERCHANT_ID', '')
MIDTRANS_CLIENT_KEY = os.getenv('MIDTRANS_CLIENT_KEY', '')
MIDTRANS_SERVER_KEY = os.getenv('MIDTRANS_SERVER_KEY', '')
MIDTRANS_IS_PRODUCTION = os.getenv('MIDTRANS_IS_PRODUCTION', 'False').strip().lower() in ('true', '1', 'yes')

KOMERCE_API_KEY = os.getenv('KOMERCE_API_KEY', '')
KOMERCE_BASE_URL = os.getenv('KOMERCE_BASE_URL', 'https://api.komerce.co.id/api/v1/shipping')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'komerce_file': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.shipping': {
            'handlers': ['console', 'komerce_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.shipping.services.komerce': {
            'handlers': ['console', 'komerce_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

if not DEBUG:
    # Jangan redirect SSL di Vercel — Vercel sudah handle HTTPS di level proxy
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
