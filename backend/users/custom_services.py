# import bcrypt
import logging
import random
import uuid

from django.contrib.auth.models import update_last_login
from django.core.mail import send_mail

from rest_framework_simplejwt.tokens import RefreshToken


# from backend.settings import EMAIL_HOST_USER


def create_token(user):
    refresh = RefreshToken.for_user(user)
    refresh.access_token.payload["aud"] = "tiles"
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# """ Creating JWT token """
# def create_token(user):
#     jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
#     jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
#     payload = jwt_payload_handler(user)
#     token = jwt_encode_handler(payload)
#     update_last_login(None, user)
#     return token


def generate_verification_code(length: int = 10):
    """
    this function return a random password
    """
    return random.randint(1000, 9999)


# def generate_salt():
#     salt_bytes = uuid.uuid4().bytes
#     salt_string = bcrypt.gensalt(prefix=b"2a", salt=salt_bytes).decode("utf-8")[4:-1]
#     return salt_string


# custome function to send emails
def mailSend(subject, recipient_list, message="", html_message=""):
    try:
        email_from = ""  # EMAIL_HOST_USER
        send_mail(
            subject, message, email_from, recipient_list, html_message=html_message
        )
        return True
    except Exception as e:
        return False


def error_payload(error):
    payload = {}
    payload["error"] = error
    return payload


def success_payload(data, token=None):
    payload = {}
    payload["content"] = data
    # send  authtoken in the response
    if token:
        payload["content"]["token"] = token
    return payload
