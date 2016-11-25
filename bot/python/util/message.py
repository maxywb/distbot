#!/usr/bin/env python3

import enum
import time

def _get_millis():
    return int(round(time.time() * 1000))

BASE_MESSAGE = """{"timestamp":"%(timestamp)s","action":"%(message_type)s","message":"%(message)s","destination":"%(destination)s"}"""

class Message():

    def __init__(self, who, where, message, private=False):
        self.message = message

        if where == "PRIVMSG":
            private = True

        if private:
            self.destination = who
            self.message_type = "PRIVMSG"
        else:
            self.destination = where
            self.message_type = "SAY"

    def __getitem__(self, item):
        return getattr(self, item)

    def wire_repr(self):
        self.timestamp = _get_millis()
        return BASE_MESSAGE % self

class Command():
    def __init__(self, action, location, message=""):
        self.message_type = action
        self.destination = location
        self.message = message

    def __getitem__(self, item):
        return getattr(self, item)

    def wire_repr(self):
        self.timestamp = _get_millis()
        return BASE_MESSAGE % self

if __name__ == "__main__":
    m = Message("user", "channel", "message")
    print(m.wire_repr())

    m = Message("user", "channel", "message", private=True)
    print(m.wire_repr())

