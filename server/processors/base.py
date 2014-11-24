# -*- coding: utf-8 -*-

import logging


class BaseProcessor(object):
    """
    Base class for user input processors that sets up redis and redis pub-sub
    connections, building a logger, and delegating input handling.

    It simplifies some calls that involve higher-level objects to shield them
    from inheritor processors.
    """

    log_key = 'Base'

    def __init__(self, user_handler, redis):
        self.user_handler = user_handler
        self.finished = False
        self.redis = redis
        self.pubsub = self.redis.pubsub()
        self.thread = None
        self.logger = logging.getLogger(__name__ + '.' + self.log_key.lower())

    def stop(self):
        if self.thread:
            self.thread.stop()
        self.redis.quit()

    def handleInput(self, line):
        if not self.isFinished():
            self.process(line)

    def process(self, line):
        raise NotImplementedError

    def log(self, level, msg):
        self.logger.log(level, "{key}: {username}: {msg}".format(key=self.log_key, username=self.username, msg=msg))

    def isFinished(self):
        return self.finished

    def activate(self):
        pass

    def send(self, line):
        self.user_handler.respondToUser(line)

    def stop(self):
        pass

    @property
    def username(self):
        return self.user_handler.username

    @property
    def uuid(self):
        return str(self.user_handler.uuid)

    def setUsername(self, username):
        self.log(logging.INFO, 'Changing username from {} to {}'.format(self.username, username))
        self.user_handler.setUsername(username)
        self.redis.sadd('users', username)
