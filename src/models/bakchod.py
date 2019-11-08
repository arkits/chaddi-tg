#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Encapsulate data representing a Bakchod
class Bakchod:

  def __init__(self, tg_id, username):

    # Telegram ID
    self.id = tg_id

    # Telegram Username
    self.username = username

    # Last seen on Telegram as a Date
    self.lastseen = None

    # Rokda. Initialized to 500
    self.rokda = 500

    # User's Birthday as a Date
    self.birthday = None

    # History Dictionary
    # key="history_type", value=Date
    self.history = {}