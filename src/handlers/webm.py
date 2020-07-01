from loguru import logger
from util import util
import traceback
import datetime
import subprocess


def handle(update, context):

    try:

        util.log_chat("webm", update)

        document = update.message.document

        if not document.file_name.endswith(".webm"):
            return

        # conversion_inform_message = update.message.reply_text(
        #     text="ヾ(＾-＾)ノ starting webm conversion!"
        # )

        try:

            time_start = datetime.datetime.now()

            # Download the webm file
            webm_file = context.bot.get_file(document.file_id)

            logger.info(
                "[webm] Starting webm download - " + str(document.file_id) + ".webm"
            )
            webm_file.download(
                "resources/webm_conversions/" + str(document.file_id) + ".webm"
            )
            logger.info("[webm] Downloaded webm - " + str(document.file_id) + ".webm")

            ffmpeg_conversion = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    "resources/webm_conversions/" + str(document.file_id) + ".webm",
                    "resources/webm_conversions/" + str(document.file_id) + ".mp4",
                ]
            )

            if ffmpeg_conversion.returncode != 0:
                logger.error(
                    "[webm] ffmpeg conversion had a non-zero return code! webm={} ffmpeg_conversion={}",
                    str(document.file_id),
                    ffmpeg_conversion,
                )
                return

            time_end = datetime.datetime.now()
            diff = time_end - time_start
            pretty_diff = util.pretty_time_delta(diff.seconds)

            logger.info(
                "[webm] ffmpeg conversion complete! webm={} time_taken={}",
                str(document.file_id),
                pretty_diff,
            )

            original_sender = util.extract_pretty_name_from_tg_user(
                update.message.from_user
            )

            caption = "{} converted your webm to mp4 in {}".format(
                original_sender, pretty_diff
            )

            context.bot.send_video(
                chat_id=update.message.chat_id,
                video=open(
                    "resources/webm_conversions/" + str(document.file_id) + ".mp4", "rb"
                ),
                timeout=5000,
                caption=caption,
            )

        except Exception as e:
            logger.error(
                "Caught Error in webm.conversion - {} \n {}", e, traceback.format_exc(),
            )

    except Exception as e:
        logger.error(
            "Caught Error in webm.handle - {} \n {}", e, traceback.format_exc(),
        )
