import os

from configurations.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_CONFIGURATION', 'Production')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot.settings.settings')

application = get_wsgi_application()
