# -*- coding: utf-8 -*-

import logging
import json
import inspect

import arrow

from .base import BaseProcessor
from .mixins import NickCommandsMixin



# Message action types
TALK = 'talk'
JOIN = 'join'
LEAVE = 'leave'


class ChatProcessor(BaseProcessor, NickCommandsMixin):
    """
    Implement chat functionality based on joining a room, exchanging messages,
    and handling basic IRC-like services.
    """

    log_key = 'Chat'

    def __init__(self, *args, **kwargs):
        super(ChatProcessor, self).__init__(*args, **kwargs)
        self.finished = False
        self.channel = None

    def stop(self):
        self.do_leave()
        if self.thread:
            self.thread.stop()
        self.pubsub.punsubscribe('*')

    def __del__(self):
        self.stop()

    def process(self, line):
        """Differentiate and handle commands and text messages"""
        msg = line.strip()
        if not msg:
            return
        self.log(logging.INFO, "Received message: {msg}".format(msg=msg))

        # commands start with /
        if msg.startswith('/'):
            cmd, trash, args = msg.partition(' ')
            self.handleCommand(cmd, args)
        else:
            self.publishMessage(msg)

    def publishMessage(self, message, action=TALK):
        if self.channel:
            self.log(logging.INFO, "Sent message to {}: {}".format(self.channel, message))
            self.redis.publish(self.channel, self._packageMsg(message, action))
        else:
            self.send("Please join a channel first.")
            self.send("Use command: /join a_channel")

    def do_join(self, channel_name):
        """Join a chat room by subscribing to it"""
        if not channel_name:
            return

        # leave current room
        if channel_name != self.channel:
            self.do_leave(quiet=True)

        self.channel = channel_name
        if self.redis.sismember(channel_name, self.username):
            self.send("You are already in {}".format(channel_name))
        else:
            self.log(logging.INFO, "Join {channel}".format(channel=channel_name))
            # add to rooms list
            self.redis.sadd('rooms', channel_name)
            # add username to room membership list
            self.redis.sadd(channel_name, self.username)

            self.send("entering room: {}".format(channel_name))
            self.do_users()
            self.publishMessage("* new user joined chat: {}".format(self.username), JOIN)
            self.pubsub.subscribe(**{channel_name: self.onMessage})
            if self.thread:
                self.thread.stop()
            self.thread = self.pubsub.run_in_thread(sleep_time=0.01)
            self.send("joined {}".format(channel_name))

    def do_users(self, args=None):
        """List users in the current room"""

        members = list(self.redis.smembers(self.channel))
        members.sort()
        lines = [' * {}'.format(username)
                    if username != self.username
                    else ' * {} (this is you)'.format(username)
                 for username in members]
        lines.insert(0, 'room members: ({} users)'.format(len(members)))
        self.send('\n'.join(lines))

    def do_room(self, args=None):
        """Tell user which room they are in"""
        if not self.channel:
            self.send("You are not in a room")
        else:
            self.send("You are in room {}".format(self.channel))

    def _packageMsg(self, text, action=TALK):
        """Helper to build publishable user action"""
        msg_packet = {
            'user': str(self.uuid),
            'username': self.username,
            'timestamp': arrow.utcnow().isoformat(),
            'action': action,
            'text': text}
        return json.dumps(msg_packet)

    def do_quit(self, args=None):
        """Leave room and mark processor as finished"""
        self.do_leave()
        self.finished = True

    def onMessage(self, message):
        """Redis callback when subscribed channel updates come in"""
        self.log(logging.INFO, "Received published message: {}".format(message))
        msg_packet = json.loads(message['data'])
        if msg_packet['action'] in (JOIN, LEAVE):
            text = str(msg_packet['text'])
        else:
            text = "{username}: {text}".format(username=msg_packet['username'], text=msg_packet['text'])
        if msg_packet['user'] != str(self.uuid):
            self.send(text)

    def do_leave(self, args=None, quiet=False):
        """Leave a channel"""
        if self.channel:
            leave_msg = " * user has left chat: {}".format(self.username)
            self.log(logging.INFO, "Left {channel}".format(channel=self.channel))
            self.publishMessage(leave_msg, LEAVE)
            self.redis.srem(self.channel, self.username)
            self.pubsub.unsubscribe(self.channel)
            if not quiet:
                self.send(leave_msg + " (** this is you)")
        self.channel = None

    def handleCommand(self, cmd, args):
        """Handle user input as a command or user-sent text message"""
        cmd = cmd.lstrip('/').split()[0].title()
        self.log(logging.INFO, "Processed command as '{cmd}' with argument '{args}'".format(cmd=cmd, args=args))
        handler_name = "do_{cmd}".format(cmd=cmd.lower())
        method = getattr(self, handler_name, None)
        if not method:
            self.send("unknown command")
        else:
            method(args)

    def activate(self):
        self.do_join('global')

    def do_rooms(self, args=None):
        """List known rooms with at least one member"""
        # get room data
        room_data = dict([
            (key, self.redis.scard(key)) for key in self.redis.smembers('rooms')])

        # format it
        lines = ["Active rooms are:", ]
        lines.extend([" * {} ({})".format(channel, size) for channel, size in room_data.items()
                        if self.redis.scard(channel) > 0])
        output = '\n'.join(lines)
        self.send(output)

    def do_help(self, args=None):
        """Detect available commands at runtime"""
        members = [method[0] for method in inspect.getmembers(self, predicate=inspect.ismethod)
                   if method[0].startswith('do_')]
        commands = [' * /' + method.replace('do_', '') for method in members]
        output = ['Available commands:']
        output.extend(commands)
        self.send('\n'.join(output))


