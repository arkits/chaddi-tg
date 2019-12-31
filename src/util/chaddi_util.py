#!/usr/bin/env python
# -*- coding: utf-8 -*-s

import logging
import config
from datetime import datetime, date, timezone

# Enable logging
logger = logging.getLogger(__name__)


# Generates a human readable time_delta
def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%dd %dh %dm %ds' % (days, hours, minutes, seconds)
    elif hours > 0:
        return '%dh %dm %ds' % (hours, minutes, seconds)
    elif minutes > 0:
        return '%dm %ds' % (minutes, seconds)
    else:
        return '%ds' % (seconds,)


# Returns whether the specified bakchod_id is a Chaddi Admin.
def is_admin(bakchod_id):
    if str(bakchod_id) in config.allowed_setters:
        logger.info("is_admin: og_bakchod in config.allowed_setters")
        return True
    else:
        return False