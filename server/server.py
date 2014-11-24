# -*- coding: utf-8 -*-

import uuid
import logging
import sys
from uuid import getnode as get_mac

from twisted.internet import reactor, protocol, endpoints
from twisted.protocols import basic
import redis

import processors
from config import REDIS, SERVER


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=SERVER['LOGFILE'], filemode='a')


class RedisConnectorMixin(object):
    def getRedisConnection(self, config):
        return redis.StrictRedis(
            password=config['PASSWORD'],
            host=config['HOST'],
            port=config['PORT'],
            db=0)


class PubProtocol(basic.LineReceiver, RedisConnectorMixin):
    """
    Pass incoming messages into a chain of command-processing objects
    that handle specific functions before being 'finished' and activating
    the next in turn.
    """
    def __init__(self, factory, redis_config):
        self.uuid = uuid.uuid4()
        self.username = self.uuid
        self.factory = factory
        self.processors = [
            processors.LoginProcessor(self, self.getRedisConnection(redis_config)),
            processors.ChatProcessor(self, self.getRedisConnection(redis_config)),
            ]
        self.current_processor = None

    def log(self, severity, msg):
        logging.log(severity, "{uuid}: {msg}".format(uuid=self.uuid, msg=msg))

    def connectionMade(self):
        self.log(logging.INFO, "New client joined".format(uuid=self.uuid))
        self.factory.clients.add(self)
        self.cycleProcessors()

    def connectionLost(self, reason):
        if self.current_processor:
            self.current_processor.stop()
        self.log(logging.INFO, "Client disconnected".format(uuid=self.uuid))
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        """Process user-sent messages with current processor object"""
        try:
            self.current_processor.handleInput(line)
        except Exception as e:
            self.log(logging.ERROR, e)
        self.cycleProcessors()

    def cycleProcessors(self):
        """Set a new active user input processor as the active one finishes"""
        if not self.current_processor or self.current_processor.isFinished():
            if not self.processors:
                self.respondToUser("Closing connection")
            else:
                self.current_processor = self.processors.pop(0)
                self.log(logging.INFO, "Activating {} processor".format(self.current_processor.log_key))
                self.current_processor.activate()

    def respondToUser(self, msg):
        """Log messages sent to user before transmitting"""
        self.log(logging.INFO, "Sent to user '{msg}'".format(msg=msg))
        self.sendLine(msg)

    def setUsername(self, username):
        self.username = username


class ClientFactory(protocol.Factory, RedisConnectorMixin):
    def __init__(self):
        self.clients = set()
        self.redis = self.getRedisConnection(REDIS)
        self.mac_id = get_mac()
        # register as a server
        self.redis.sadd('servers', self.mac_id)

    def buildProtocol(self, addr):
        return PubProtocol(self, REDIS)

    def reset_db(self):
        self.redis.flushdb()

    def __del__(self):
        # deregister server
        self.redis.srem('servers', self.mac_id)

        # stop clients
        for client in self.clients:
            del self.clients[client]


if __name__ == '__main__':
    print("Starting server on port 9399")
    logger.info("Starting server on port 9399")
    factory = ClientFactory()
    endpoints.serverFromString(reactor, "tcp:{}".format(SERVER['PORT'])).listen(factory)
    if '-noclear' not in sys.argv:
        print("Clearing redis DB")
        logger.info("Clearing redis DB")
        factory.reset_db()

    reactor.run()
