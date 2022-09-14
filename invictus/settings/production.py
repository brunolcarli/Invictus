import os
from invictus.settings.common import *


# SECRET_KEY = os.environ.get('SECRET_KEY', '')
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': os.environ.get('MYSQL_DATABASE', ''),
        'USER': os.environ.get('MYSQL_USER', ''),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),
        'HOST': os.environ.get('MYSQL_HOST', ''),
        'PORT': os.environ.get('MYSQL_PORT'),
        'OPTIONS': {
          'autocommit': True,
        }
    }
}
