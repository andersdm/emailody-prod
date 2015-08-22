import os

import redis
from rq import Worker, Queue, Connection

listen = ['default']

redis_url = os.getenv('redis://redistogo:7620d3347def4ab785738bb18ec7fcc5@tarpon.redistogo.com:10955/', 'redis://localhost:6379')

conn = redis.from_url(redis_url)



if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()

