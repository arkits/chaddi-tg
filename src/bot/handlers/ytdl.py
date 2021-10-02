from __future__ import unicode_literals
from loguru import logger
from telegram import Update
from src.domain import dc, util, config
import youtube_dl
import traceback
import os
import multiprocessing


app_config = config.get_config()

YTDL_MAX_DOWNLOAD_TIME = app_config.get("TELEGRAM", "YTDL_MAX_DOWNLOAD_TIME")

YTDL_OPTS = {
    "outtmpl": os.path.join(util.RESOURCES_DIR, "external", "%(id)s"),
    "merge_output_format": "mp4",
}

ydl = youtube_dl.YoutubeDL(YTDL_OPTS)


def handle(
    update: Update,
    context,
):

    dc.log_command_usage("ytdl", update)

    try:

        message_text = update.message.text
        message_params = message_text.split(" ")

        video_url = message_params[1]
        logger.info("[ytdl] video_url={}", video_url)

        message = update.message.reply_text("Downloading video via youtube-dl (＠＾◡＾)")

        try:

            video_info = ydl.extract_info(video_url, download=False)
            logger.debug("[ytdl] video_info={}", video_info)

            p_killed = False

            p = multiprocessing.Process(target=download_video, args=(video_url,))
            p.start()  # Process(...) is not yet running.

            p.join(YTDL_MAX_DOWNLOAD_TIME)

            # If thread is active
            if p.is_alive():

                logger.debug("[ytdl] killing process")

                p_killed = True

                # Terminate foo
                p.terminate()
                p.join()

            if p_killed:
                message.edit_text(
                    "Download cancelled... took too long ヽ(`⌒´メ)ノ Try again with please (⌒_⌒;)"
                )
                return

            downloaded_video_path = os.path.join(
                util.RESOURCES_DIR, "external", video_info["id"] + ".mp4"
            )

            caption = """
{}
URL: {}
""".format(
                video_info["title"],
                video_url,
            )

            logger.debug("[ytdl] replying to the request message with downloaded video")
            message.edit_text("Uploading video (－.－)...zzz")
            update.message.reply_video(
                timeout=5000,
                video=open(downloaded_video_path, "rb"),
                caption=caption,
            )

            message.delete()
            util.delete_file(downloaded_video_path)

        except Exception as e:
            logger.error("[ytdl] Caught error in ytdl download e={}", e)
            message.edit_text("Error downloading the video! (〃＞＿＜;〃)")
            raise e

    except Exception as e:
        logger.warning(
            "Caught error in ytdl.handle. e={} traceback={}",
            e,
            traceback.format_exc(),
        )
        return


def download_video(video_url):

    logger.debug("[ytdl] starting download video_url={}", video_url)
    download_info = ydl.download([video_url])
    logger.debug("[ytdl] finished download download_info={}", download_info)

    return download_info