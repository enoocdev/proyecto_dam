import secrets
# Genera una cadena segura para usar en URLs
url_safe_token = secrets.token_urlsafe(32)
print(url_safe_token)

