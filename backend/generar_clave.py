import secrets
# Genera un token seguro para usar como clave secreta de Django
url_safe_token = secrets.token_urlsafe(32)
print(url_safe_token)

