import os

PORT = int(os.environ.get('PORT', 8000))
APP_ENV = os.environ.get('ENV', 'development')
TIMEOUT = 30
