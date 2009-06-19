import os, sys, site

# enable the virtualenv
site.addsitedir('/var/www/modus/modus/ve/lib/python2.5/site-packages')

# paths we might need to pick up the project's settings
sys.path.append('/var/www/')
sys.path.append('/var/www/modus/')
sys.path.append('/var/www/modus/modus/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'modus.settings_production'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
