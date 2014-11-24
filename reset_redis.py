import redis
redis = redis.StrictRedis(password='weeby', host='pub-redis-17292.us-east-1-3.4.ec2.garantiadata.com', port=17292, db=0)
redis.flushdb()

