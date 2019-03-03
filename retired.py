#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################
#                         ChaddiBot                               #
#                        Archit Khode                             #
###################################################################

def awk(bot, update):
    # Handle /awk
    # /awk is a handle that would return the time since AwkDev was absent in Feb 2019.
    logger.info('Sending /awk response')

    # response = util.awk_timer()
    # update.message.reply_text(text='<b>Time since AwkDev goned:</b> ' + response , parse_mode=ParseMode.HTML)
    
    update.message.reply_text(text='<b>Time since AwkDev goned:</b> 21d 0h 24m 22s' , parse_mode=ParseMode.HTML)


def job_spam(bot, job):
    # Job Spam is a repeating job.
    # It will randomly message a person in the group.
    
    logger.info('job_spam: Running job_spam')

    if config.is_dev is False:
        bot.send_message(chat_id=config.true_chat_id, text=util.random_user('true'))
        bot.send_message(chat_id=config.mains_chat_id, text=util.random_user('mains'))
        random_job_interval = random.randint(130,180) 
    else:
        bot.send_message(chat_id=config.test_chat_id, text=util.random_user('mains'))
        random_job_interval = 0.2

    logger.info('Setting next interval to ' + str(random_job_interval) + ' mins')
    job.interval = random_job_interval * 60