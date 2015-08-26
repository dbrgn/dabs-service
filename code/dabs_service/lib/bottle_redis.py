"""
Source: https://github.com/bottlepy/bottle-extras/tree/master/redis

Copyright (c) 2013 Sean M. Collins

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
import inspect
from urlparse import urlparse

import redis
from bottle import PluginError


class RedisPlugin(object):
    name = 'redis'
    api = 2

    def __init__(self, redis_url='redis://localhost:6379/0', keyword='rdb'):
        url = urlparse(redis_url)
        assert url.scheme == 'redis' or not url.scheme
        self.host = url.hostname
        self.port = int(url.port or 6379)
        self.password = url.password or None
        try:
            self.database = int(url.path.replace('/', ''))
        except (AttributeError, ValueError):
            self.database = 0
        self.keyword = keyword
        self.redisdb = None

    def setup(self, app):
        for other in app.plugins:
            if not isinstance(other, RedisPlugin):
                continue
            if other.keyword == self.keyword:
                raise PluginError("Found another redis plugin with " +
                        "conflicting settings (non-unique keyword).")
        if self.redisdb is None:
            self.redisdb = redis.ConnectionPool(host=self.host, port=self.port,
                                                password=self.password, db=self.database)

    def apply(self, callback, route):
        conf = route.config.get('redis') or {}
        args = inspect.getargspec(route.callback)[0]
        keyword = conf.get('keyword', self.keyword)
        if keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            kwargs[self.keyword] = redis.StrictRedis(connection_pool=self.redisdb)
            rv = callback(*args, **kwargs)
            return rv
        return wrapper

Plugin = RedisPlugin
