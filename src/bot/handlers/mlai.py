from os import path
import os
import traceback
import boto3
from telegram import Update
from telegram.parsemode import ParseMode
from src.domain import dc, util
from loguru import logger
from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
import uuid

rekognition_client = boto3.client("rekognition")

MLAI_RESOURCES_DIR = path.join(util.RESOURCES_DIR, "mlai")
PNG_EXTENSION = ".png"


def handle(update: Update, context):

    try:

        dc.log_command_usage("mlai", update)

        reply_text = """
*chaddi-ai Facial Analysis \n*
"""

        file = acquire_file(update, context)

        logger.info("[mlai] Running rekognition on file_id={}", file["file_id"])
        with open(
            MLAI_RESOURCES_DIR + file["file_id"] + file["extension"], "rb"
        ) as photo_file:
            response = rekognition_client.detect_faces(
                Image={"Bytes": photo_file.read()}, Attributes=["ALL"]
            )
            logger.debug("[mlai] response={}", response)

        # Draw bounding boxes on the image
        image = Image.open(build_file_path(file))
        img_width, img_height = image.size
        draw = ImageDraw.Draw(image)

        reply_text += "- Number of Faces detected: {} \n".format(
            len(response["FaceDetails"])
        )

        for idx, face_detail in enumerate(response["FaceDetails"]):

            reply_text += """
* Face #{}*
- Gender: {}
- Age Range: between {} and {}
- Smile: {}
- Emotions: {}
""".format(
                idx + 1,
                face_detail["Gender"]["Value"],
                face_detail["AgeRange"]["Low"],
                face_detail["AgeRange"]["High"],
                face_detail["Smile"]["Value"],
                list_out_emotions(face_detail["Emotions"]),
            )

            box = face_detail["BoundingBox"]

            draw_bounding_box(draw, box, img_width, img_height)

        image.save(MLAI_RESOURCES_DIR + file["file_id"] + "_mlai" + PNG_EXTENSION)

        reply_text = reply_text[
            :1024
        ]  # truncate to Telegram's size limit for media caption

        with open(
            MLAI_RESOURCES_DIR + file["file_id"] + "_mlai" + PNG_EXTENSION, "rb"
        ) as photo_to_upload:
            update.message.reply_photo(
                photo=photo_to_upload,
                caption=reply_text,
                parse_mode=ParseMode.MARKDOWN,
            )

        # Cleanup the downloaded files
        util.delete_file(build_file_path(file))
        util.delete_file(build_file_path(file, "_mlai"))

    except Exception as e:
        logger.error(
            "Caught Error in mlai.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )


def handle_ocr(update: Update, context):

    try:

        reply_text = """
*chaddi-ai OCR \n*
"""

        dc.log_command_usage("mlai-ocr", update)

        file = acquire_file(update, context)

        logger.info("[mlai] Running rekognition on file_id={}", file["file_id"])
        with open(
            MLAI_RESOURCES_DIR + file["file_id"] + file["extension"], "rb"
        ) as photo_file:
            response = rekognition_client.detect_text(
                Image={"Bytes": photo_file.read()}
            )
            logger.debug("[mlai] response={}", response)

        text_detections = response["TextDetections"]
        reply_text += "- Elements detected: {} \n \n".format(len(text_detections))

        for idx, text in enumerate(text_detections):

            if text["Type"] != "WORD":
                continue

            reply_text += "{} ".format(text["DetectedText"])

        reply_text = reply_text[:4096]  # truncate to Telegram's max size
        update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

        util.delete_file(build_file_path(file))

        return

    except Exception as e:
        logger.error(
            "Caught Error in mlai.handle_ocr - {} \n {}",
            e,
            traceback.format_exc(),
        )


def acquire_file(update: Update, context):

    # Extract file ID from update
    file_id = str(
        update.message.reply_to_message.photo[-1].file_id
    )  # TODO: handle video and gifs?

    logger.info("[mlai] Starting file download file_id={}", file_id)
    file_handle = context.bot.get_file(file_id)
    file_handle.download(MLAI_RESOURCES_DIR + file_id + PNG_EXTENSION)

    return {"file_id": file_id, "extension": PNG_EXTENSION}


def build_file_path(file, file_name_suffix=""):
    return MLAI_RESOURCES_DIR + file["file_id"] + file_name_suffix + file["extension"]


def list_out_emotions(emotions):

    toReturn = ""

    for emotion in emotions:
        toReturn += "{} ({}%); ".format(
            emotion["Type"], round(emotion["Confidence"], 2)
        )

    return toReturn


def draw_bounding_box(draw, box, img_width, img_height):

    left = img_width * box["Left"]
    top = img_height * box["Top"]
    width = img_width * box["Width"]
    height = img_height * box["Height"]

    points = (
        (left, top),
        (left + width, top),
        (left + width, top + height),
        (left, top + height),
        (left, top),
    )

    draw.line(points, fill="#00d400", width=2)

    return draw
