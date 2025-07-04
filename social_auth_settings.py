# Social Authentication Settings

# 设置正确的站点 ID (使用 infs3202-183b16dd.uqcloud.net 的 ID)
SITE_ID = 2

# 认证后端
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# GitHub OAuth 设置
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': [
            'user',
            'read:user',
            'user:email',
        ],
    }
}

# 社交账号基本设置
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_REDIRECT_URL = 'index'
LOGIN_REDIRECT_URL = 'menu_welcome' 