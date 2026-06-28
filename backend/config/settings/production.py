import os
from urllib.parse import urlparse
from .base import *

DEBUG = False

# Read database URL or fallback
database_url = os.getenv('DATABASE_URL')

if database_url:
    url = urlparse(database_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'postgres',
            'USER': 'postgres.wmubfnopsxbimpwhhlbv',
            'PASSWORD': 'HaGkfWg7EeDP9GNA',
            'HOST': 'aws-1-us-west-1.pooler.supabase.com',
            'PORT': '6543',
        }
    }
