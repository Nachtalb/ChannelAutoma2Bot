import os
from pathlib import Path

import dotenv

env_path = Path(__file__).absolute().parent.parent / '.env'

dotenv.read_dotenv(env_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot.settings.settings')

from configurations.wsgi import get_wsgi_application

application = get_wsgi_application()
