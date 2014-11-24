# -*- coding: utf-8 -*-

import logging

from .base import BaseProcessor


class LoginProcessor(BaseProcessor):
    """
    Handle login actions by asking for a unique username until
    user provides one.
    """

    log_key = 'Login'

    def __init__(self, *args, **kwargs):
        super(LoginProcessor, self).__init__(*args, **kwargs)

    def process(self, line):
        """Ask user repeatedly until a unique, available username is provided"""
        line = line.strip()
        self.log(logging.INFO, "Proposed username '{line}'".format(line=line))
        if self.isValidUsername(line):
            self.send("Usernames must be a single word of letters and numbers")
            self.askUsername()
            return
        if self.isUsernameAvailable(line):
            self.send("Sorry, name taken.")
            self.askUsername()
            return
        self.setUsername(line)
        self.welcomeUser()
        self.finished = True

    def activate(self):
        """Immediately ask for username"""
        self.askUsername()

    def askUsername(self):
        self.send("Login Name?")

    def welcomeUser(self):
        self.send("Welcome {name}!".format(name=self.username))

    def isValidUsername(self, name):
        """Check username against basic rules"""
        # this is a terrible way to do this...use regex probably
        return ' ' in name or '/' in name

    def isUsernameAvailable(self, name):
        return self.redis.sismember('users', name)
