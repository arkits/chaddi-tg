from loguru import logger
from peewee import Update
from src.domain import dc, util
import datetime
import subprocess
import traceback

WEBM_RESOURCES_DIR = "resources/webm_conversions/"


def handle(update: Update, context):

    try:

        document = update.message.document

        # return if the document isn't a webm
        if not document.file_name.endswith(".webm"):
            return

        dc.log_command_usage("webm", update)

        try:

            # Count time taken for webm conversion
            time_start = datetime.datetime.now()

            # Download the webm file
            logger.info(
                "[webm] Starting webm download - " + str(document.file_id) + ".webm"
            )
            webm_file = context.bot.get_file(document.file_id)
            webm_file.download(WEBM_RESOURCES_DIR + str(document.file_id) + ".webm")
            logger.info(
                "[webm] Finished downloading webm - " + str(document.file_id) + ".webm"
            )

            # Webm to mp4 conversion via ffmpeg
            logger.info(
                "[webm] Starting webm conversion with ffmpeg - "
                + str(document.file_id)
                + ".webm"
            )

            ffmpeg_conversion = subprocess.call(
                "ffmpeg -i "
                + WEBM_RESOURCES_DIR
                + str(document.file_id)
                + '.webm -vcodec libx264 -crf 28 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" '
                + WEBM_RESOURCES_DIR
                + str(document.file_id)
                + ".mp4",
                shell=True,
            )

            if ffmpeg_conversion != 0:
                logger.error(
                    "[webm] ffmpeg conversion had a non-zero return code! webm={} ffmpeg_conversion={}",
                    str(document.file_id),
                    ffmpeg_conversion,
                )
                update.message.reply_text(
                    text="(｡•́︿•̀｡) webm conversion failed (｡•́︿•̀｡)"
                )
                return

            # Calculate time taken to convert
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

            caption = random_webm_caption(
                original_sender, pretty_diff, document.file_name, update.message.caption
            )

            logger.info(
                "[webm] sending converted video webm={} caption={}",
                str(document.file_id),
                caption,
            )
            context.bot.send_video(
                chat_id=update.message.chat_id,
                video=open(WEBM_RESOURCES_DIR + str(document.file_id) + ".mp4", "rb"),
                timeout=5000,
                caption=caption,
            )

            util.delete_file(WEBM_RESOURCES_DIR + str(document.file_id) + ".webm")
            util.delete_file(WEBM_RESOURCES_DIR + str(document.file_id) + ".mp4")

        except Exception as e:
            logger.error(
                "Caught Error in webm.conversion - {} \n {}",
                e,
                traceback.format_exc(),
            )

    except Exception as e:
        logger.error(
            "Caught Error in webm.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )


def random_webm_caption(original_sender, pretty_diff, file_name, caption_text):
    strings = [
        "{} uploaded {}".format(original_sender, file_name)
    ]

    if caption_text is not None:
        strings.append("\n------------------------------------\n{}\n------------------------------------".format(caption_text))

    strings.append("\n(converted in {})".format(pretty_diff))

    return " ".join(strings)
