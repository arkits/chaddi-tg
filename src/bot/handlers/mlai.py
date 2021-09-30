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
EXTERNAL_DIR = path.join(util.RESOURCES_DIR, "external")

PNG_EXTENSION = ".png"
NM_IMG_URL = "https://i.imgur.com/QAUObo1.png"


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


def handle_tynm(update: Update, context):

    try:

        dc.log_command_usage("mlai-tynm", update)

        if update.message.reply_to_message is None:
            update.message.reply_text("Please reply to a message with `/tynm`")
            return

        util.acquire_external_resource(NM_IMG_URL, "nm.png")

        if update.message.reply_to_message.photo:

            file = acquire_file(update, context)

            src_img = Image.open(build_file_path(file))
            src_img_width, src_img_height = src_img.size
            logger.debug(
                "src_img_width={} src_img_height={}", src_img_width, src_img_height
            )

            nm_img = Image.open(path.join(EXTERNAL_DIR, "nm.png"))

            place_image(src_img, nm_img)

            src_img.save(build_file_path(file, "_tynm"))

            with open(build_file_path(file, "_tynm"), "rb") as photo_to_upload:
                logger.info("[tynm] uploading completed photo")
                update.message.reply_photo(
                    photo=photo_to_upload,
                    caption="🙏 THANK YOU 🙏",
                    parse_mode=ParseMode.MARKDOWN,
                )

            util.delete_file(build_file_path(file))
            util.delete_file(build_file_path(file, "_tynm"))

        if update.message.reply_to_message.text:

            unsplash_photo_path = None

            text = update.message.reply_to_message.text

            random_font_caption = util.choose_random_element_from_list(
                [
                    "Merriweather-Regular.ttf",
                    "AmaticSC-Regular.ttf",
                    "Italianno-Regular.ttf",
                ]
            )

            font_caption = ImageFont.truetype(
                path.join(
                    os.getcwd(), util.RESOURCES_DIR, "fonts", random_font_caption
                ),
                35,
            )

            font_subtitle = ImageFont.truetype(
                path.join(
                    os.getcwd(), util.RESOURCES_DIR, "fonts", random_font_caption
                ),
                25,
            )

            random_font_username = util.choose_random_element_from_list(
                [
                    "Merriweather-Regular.ttf",
                    "AmaticSC-Regular.ttf",
                    "Italianno-Regular.ttf",
                    "BebasNeue-Regular.ttf",
                ]
            )
            font_username = ImageFont.truetype(
                path.join(
                    os.getcwd(), util.RESOURCES_DIR, "fonts", random_font_username
                ),
                50,
            )

            # variables for image size
            x1 = 1280
            y1 = 720

            img = Image.new("RGBA", (x1, y1), color=(0, 0, 0))

            # Add unsplash background
            try:

                # Download image from unsplash
                unsplash_img_url = "https://source.unsplash.com/random/{}x{}/?nature,water,india".format(
                    x1, y1
                )

                unsplash_photo_path = util.acquire_external_resource(
                    unsplash_img_url, "{}.jpg".format(uuid.uuid4())
                )
                unsplash_photo = Image.open(unsplash_photo_path).resize((x1, y1))

                unsplash_photo_holder = Image.new("RGBA", (x1, y1), color=(0, 0, 0))
                unsplash_photo_holder.paste(unsplash_photo, (0, 0))

                img = Image.blend(img, unsplash_photo_holder, 0.1)

            except Exception as e:
                logger.warning(
                    "Caught error in unsplash background composition. e={} traceback={}",
                    e,
                    traceback.format_exc(),
                )

            # Add user profile picture background
            try:

                # User profile picture composition
                user_id = update.message.reply_to_message.from_user.id
                user_profile_photo_path = path.join(
                    EXTERNAL_DIR, str(user_id) + ".webp"
                )

                user_profile_photo = (
                    update.message.reply_to_message.from_user.get_profile_photos(
                        limit=1
                    ).photos[0]
                )
                user_profile_photo_file_id = user_profile_photo[-1].file_id
                user_profile_photo_file = context.bot.getFile(
                    user_profile_photo_file_id
                )
                user_profile_photo_file.download(user_profile_photo_path)

                user_profile_photo_img = (
                    Image.open(user_profile_photo_path).convert("RGBA").resize((y1, y1))
                )

                user_profile_photo_holder = Image.new("RGBA", (x1, y1), color=(0, 0, 0))
                user_profile_photo_holder.paste(user_profile_photo_img, (0, 0))

                gradient_mask = (
                    Image.open(path.join(util.RESOURCES_DIR, "img", "gradient_h.jpg"))
                    .convert("L")
                    .resize(img.size)
                )

                img = Image.composite(user_profile_photo_holder, img, gradient_mask)

                util.delete_file(user_profile_photo_path)

            except Exception as e:
                logger.warning(
                    "Caught error in user profile picture background. e={} traceback={}",
                    e,
                    traceback.format_exc(),
                )

            draw = ImageDraw.Draw(img)

            # Generate the caption
            caption = generate_wrapped_caption(text)
            caption_w, caption_h = draw.textsize(caption, font=font_caption)

            # Generate the username
            username = "~ " + util.extract_pretty_name_from_tg_user(
                update.message.reply_to_message.from_user
            )
            username_w, username_h = draw.textsize(username, font=font_username)

            # Generate the timestamp of the message
            timestamp = update.message.reply_to_message.date
            timestamp_str = timestamp.strftime("%m/%d/%Y, %H:%M:%S")
            timestamp_str += "\n {}".format(update.message.reply_to_message.chat.title)
            timestamp_w, timestamp_h = draw.textsize(timestamp_str, font=font_subtitle)

            # Calculate the position of the caption
            caption_x, caption_y = 100, (y1 / 2) - (
                (caption_h + username_h + timestamp_h + 20 + 10) / 2
            )

            # Draw the caption
            draw.text(
                (caption_x, caption_y), caption, font=font_caption, fill=(255, 255, 255)
            )

            # Draw the username
            draw.text(
                (caption_x, caption_y + caption_h + 20),
                username,
                font=font_username,
                fill=(255, 255, 255),
            )

            # Draw the timestamp
            draw.text(
                (caption_x, caption_y + caption_h + 20 + username_h + 10),
                timestamp_str,
                font=font_subtitle,
                fill=(255, 255, 255),
            )

            # nm_image composition
            nm_img = Image.open(path.join(EXTERNAL_DIR, "nm.png"))
            place_image(
                img,
                nm_img,
            )

            # Generate filename and file path
            filename = "{}-{}".format(update.message.chat.id, update.message.message_id)
            img_path = path.join(EXTERNAL_DIR, filename + PNG_EXTENSION)

            # Save the image
            img.save(img_path)

            with open(img_path, "rb") as photo_to_upload:
                logger.info("[tynm] uploading completed photo")
                update.message.reply_photo(
                    photo=photo_to_upload,
                    caption="🙏 THANK YOU 🙏",
                    parse_mode=ParseMode.MARKDOWN,
                )

            util.delete_file(img_path)
            util.delete_file(unsplash_photo_path)

        return

    except Exception as e:
        logger.error(
            "Caught Error in mlai.handle_tynm - {} \n {}",
            e,
            traceback.format_exc(),
        )


def generate_wrapped_caption(text):

    caption = ""

    lines = text.split("\n")

    for line in lines:

        if len(line) > 65:

            w = textwrap.TextWrapper(width=65, break_long_words=False)
            line = "\n".join(w.wrap(line))

        caption += line + "\n"

    logger.debug("caption={}", caption)

    return caption


def place_image(src_img: Image, placement_img: Image, scale=2, location="bottom_right"):

    src_img_width, src_img_height = src_img.size
    placement_img_width, placement_img_height = placement_img.size

    logger.debug(
        "original placement_img_width={} placement_img_height={}",
        placement_img_width,
        placement_img_height,
    )

    # resize nm_img to match the size of the img
    placement_img = ImageOps.contain(
        placement_img,
        (int(src_img_width / scale), int(src_img_height / scale)),
        Image.ANTIALIAS,
    )

    placement_img_width, placement_img_height = placement_img.size
    logger.debug(
        "after resize placement_img_width={} placement_img_height={}",
        placement_img_width,
        placement_img_height,
    )

    if location == "bottom_right":

        src_img.paste(
            placement_img,
            (src_img_width - placement_img_width, src_img_height - placement_img_width),
            placement_img,
        )

    elif location == "bottom_left":

        src_img.paste(
            placement_img,
            (0, src_img_height - placement_img_height),
            placement_img,
        )

    return


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
