#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Encapsulate data representing a Group
class Group:

  def __init__(self, tg_id, group_title):

    # Telegram ID
    self.id = tg_id

    # Group Title
    self.title = group_title

    # List of group member IDs
    self.members = []
    