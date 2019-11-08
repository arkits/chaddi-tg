#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Encapsulate data representing a Bakchod
class Group:
  def __init__(self, tg_id, group_title):
    self.id = tg_id
    self.title = group_title
    self.members = []
    