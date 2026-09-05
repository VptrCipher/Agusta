"""
WSGI config for agusta project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from apps.common.logging import configure_process_file_logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agusta.settings')

application = get_wsgi_application()
configure_process_file_logging("django")
