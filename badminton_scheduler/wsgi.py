"""
WSGI config for Badminton Scheduler.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""
import os
from .app import app as application  # noqa

if __name__ == "__main__":
    application.run()
