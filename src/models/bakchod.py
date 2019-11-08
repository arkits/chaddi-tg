#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Encapsulate data representing a Bakchod
class Bakchod:
  def __init__(self, tg_id, username):
    self.id = tg_id
    self.username = username
    self.lastseen = None
    self.rokda = 500
    self.birthday = None