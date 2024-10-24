import redis

# Redis connection setup
r = redis.Redis(host='localhost', port=6379, db=0)
