#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Encapsulate data representing a Bakchod
class Bakchod:

    def __init__(self, id, username, contact_name):

        # Telegram ID
        self.id = id

        # Telegram Username
        self.username = username

        # Telegram Username
        self.contact_name = contact_name

        # Last seen on Telegram as a Date
        self.lastseen = None

        # Rokda. Initialized to 500
        self.rokda = 500

        # User's Birthday as a Date
        self.birthday = None

        # History Dictionary
        # key="history_type", value=Date
        self.history = {}

        self.censored = False

    @classmethod
    def fromUpdate(cls, update):

        id = update.message.from_user.id
        username = update.message.from_user.username
        contact_name = update.message.from_user.first_name

        return cls(id, username, contact_name)
