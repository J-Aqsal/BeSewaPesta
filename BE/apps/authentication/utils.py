import jwt

from django.conf import settings


def decodeJwtToken(token):

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )

        return payload

    except:
        return None