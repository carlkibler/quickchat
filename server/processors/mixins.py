# -*- coding: utf-8 -*-


class NickCommandsMixin(object):
    """Mixing for useful username-related commands"""
    def do_nick(self, args=None):
        """Inform user of their current username"""
        if args:
            # this really should handle args != None and change username
            pass
        self.send("Your username is {}".format(self.username))

    def do_whoami(self, args=None):
        self.do_nick()
