import os
import sys

path = '/home/ваш_username/ваша_папка_проекта'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'carcost.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()