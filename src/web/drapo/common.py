from django.utils import crypto


def generate_random_secret_string():
    return crypto.get_random_string(length=32)
