# -*- coding: utf-8 -*-
import os

SERVER = {
    'PORT': 9399,
    'LOGFILE': os.path.join(os.getcwd(), 'server.log')
    }

REDIS = {
    'HOST': 'pub-redis-17292.us-east-1-3.4.ec2.garantiadata.com',
    'PASSWORD': '',
    'PORT': 17292,
    }
