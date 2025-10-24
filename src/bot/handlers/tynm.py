import datetime
import os
import random
import textwrap
import traceback
import uuid
from os import path

from loguru import logger
from PIL import Image, ImageDraw, ImageFont, ImageOps
from telegram import Update
from telegram.ext import ContextTypes

from src.domain import dc, util

MLAI_RESOURCES_DIR = path.join(util.RESOURCES_DIR, "mlai")
EXTERNAL_DIR = path.join(util.RESOURCES_DIR, "external")
FONTS_DIR = path.join(util.RESOURCES_DIR, "fonts")
PNG_EXTENSION = ".png"
NM_IMG_URLS = [
    "https://i.imgur.com/QAUObo1.png",
    "https://i.imgur.com/7iPnewL.png",
    "https://i.imgur.com/Ki85sni.png",
    "https://i.imgur.com/cP00Tbt.png",
    "https://i.imgur.com/AqauTol.png",
    "https://i.imgur.com/Cqw8yWb.png",
    "https://i.imgur.com/rpyGAWw.png",
    "https://i.imgur.com/U9JUnNO.png",
]
NM_IMG_LOCATIONS = ["bottom_right", "bottom_left"]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("tynm", update)

        if update.message.reply_to_message is None:
            await update.message.reply_text("Please reply to a message with `/tynm`")
            return

        # Choose NM_IMG
        NM_IMG_URL = random.choice(NM_IMG_URLS)
        NM_IMG_NAME = NM_IMG_URL.split("/")[-1]
        logger.debug("NM_IMG_URL={} NM_IMG_NAME={}", NM_IMG_URL, NM_IMG_NAME)
        util.acquire_external_resource(NM_IMG_URL, NM_IMG_NAME)
        nm_img = Image.open(path.join(EXTERNAL_DIR, NM_IMG_NAME))

        # Handle photo message
        if update.message.reply_to_message.photo:
            file = await acquire_file(update, context)

            src_img = Image.open(build_file_path(file))
            src_img_width, src_img_height = src_img.size
            logger.debug("src_img_width={} src_img_height={}", src_img_width, src_img_height)

            # Place NM_IMG
            nm_img_location = random.choice(NM_IMG_LOCATIONS)
            place_image(src_img, nm_img, location=nm_img_location)

            src_img.save(build_file_path(file, "_tynm"))

            with open(build_file_path(file, "_tynm"), "rb") as photo_to_upload:
                logger.info("[tynm] uploading completed photo")
                await update.message.reply_photo(
                    photo=photo_to_upload,
                )

            util.delete_file(build_file_path(file))
            util.delete_file(build_file_path(file, "_tynm"))

        # Handle text message
        elif update.message.reply_to_message.text:
            unsplash_photo_path = None

            text = update.message.reply_to_message.text

            # variables for image size
            x1 = 1280
            y1 = 720

            img = Image.new("RGBA", (x1, y1), color=(0, 0, 0))

            # Add unsplash background
            try:
                # Download image from unsplash
                unsplash_img_url = (
                    f"https://source.unsplash.com/random/{x1}x{y1}/?nature,water,india"
                )

                unsplash_photo_path = util.acquire_external_resource(
                    unsplash_img_url, f"{uuid.uuid4()}.jpg"
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
                user_profile_photo_path = path.join(EXTERNAL_DIR, str(user_id) + ".webp")

                user_profile_photos = (
                    await update.message.reply_to_message.from_user.get_profile_photos(limit=1)
                )
                user_profile_photo = user_profile_photos.photos[0]
                user_profile_photo_file_id = user_profile_photo[-1].file_id
                user_profile_photo_file = await context.bot.get_file(user_profile_photo_file_id)
                await user_profile_photo_file.download_to_drive(user_profile_photo_path)

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

            # Add dark background overlay
            dark_bg = Image.new("RGBA", (x1, y1), color=(0, 0, 0, 150))
            img = Image.alpha_composite(img, dark_bg)

            draw = ImageDraw.Draw(img)

            # Generate the caption
            caption = generate_wrapped_caption(text)

            # Setup fonts
            number_of_lines = len(caption.split("\n"))
            logger.info("number_of_lines={}", number_of_lines)

            if 0 < number_of_lines < 5:
                font_caption_size = 75
                font_username_size = 60
                font_subtitle_size = 40
            elif 5 <= number_of_lines < 10:
                font_caption_size = 45
                font_username_size = 40
                font_subtitle_size = 30
            else:
                font_caption_size = 35
                font_username_size = 40
                font_subtitle_size = 30

            logger.debug(
                "font_caption_size={} font_username_size={} font_subtitle_size={}",
                font_caption_size,
                font_username_size,
                font_subtitle_size,
            )

            random_font_caption = util.choose_random_element_from_list(os.listdir(FONTS_DIR))

            random_font_username = util.choose_random_element_from_list(os.listdir(FONTS_DIR))

            logger.debug(
                "random_font_caption={} random_font_username={}",
                random_font_caption,
                random_font_username,
            )

            font_caption = ImageFont.truetype(
                path.join(os.getcwd(), util.RESOURCES_DIR, "fonts", random_font_caption),
                font_caption_size,
            )

            font_subtitle = ImageFont.truetype(
                path.join(os.getcwd(), util.RESOURCES_DIR, "fonts", random_font_username),
                font_subtitle_size,
            )

            font_username = ImageFont.truetype(
                path.join(os.getcwd(), util.RESOURCES_DIR, "fonts", random_font_username),
                font_username_size,
            )

            caption_w, caption_h = draw.textsize(caption, font=font_caption)

            # Generate the username
            username = "~ " + util.extract_pretty_name_from_tg_user(
                update.message.reply_to_message.from_user
            )
            username_w, username_h = draw.textsize(username, font=font_username)

            # Generate the timestamp of the message
            timestamp = util.normalize_datetime(update.message.reply_to_message.date)
            timestamp_str = timestamp.strftime("%d/%m/%Y, %I:%M %p")
            timestamp_str += f"\n {update.message.reply_to_message.chat.title}"
            timestamp_w, timestamp_h = draw.textsize(timestamp_str, font=font_subtitle)

            # Calculate the position of the caption
            caption_x, caption_y = (
                100,
                (y1 / 2) - ((caption_h + username_h + timestamp_h + 20 + 10) / 2),
            )

            # Draw the caption
            draw.text((caption_x, caption_y), caption, font=font_caption, fill=(255, 255, 255))

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
            place_image(
                img,
                nm_img,
            )

            # Generate filename and file path
            filename = f"{update.message.chat.id}-{update.message.message_id}"
            img_path = path.join(EXTERNAL_DIR, filename + PNG_EXTENSION)

            # Save the image
            img.save(img_path)

            with open(img_path, "rb") as photo_to_upload:
                logger.info("[tynm] uploading completed photo")
                await update.message.reply_photo(
                    photo=photo_to_upload,
                )

            util.delete_file(img_path)
            util.delete_file(unsplash_photo_path)

        return

    except Exception as e:
        logger.error(
            "Caught Error in handle_tynm - {} \n {}",
            e,
            traceback.format_exc(),
        )


def generate_wrapped_caption(text):
    caption = ""

    lines = text.split("\n")

    for line in lines:
        if len(line) > 65:
            w = textwrap.TextWrapper(width=60, break_long_words=False)
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
        placement_img = ImageOps.mirror(placement_img)

        src_img.paste(
            placement_img,
            (0, src_img_height - placement_img_height),
            placement_img,
        )

    return


async def acquire_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Extract file ID from update
    file_id = str(update.message.reply_to_message.photo[-1].file_id)  # TODO: handle video and gifs?

    logger.info("[tynm] Starting file download file_id={}", file_id)
    file_handle = await context.bot.get_file(file_id)
    await file_handle.download_to_drive(MLAI_RESOURCES_DIR + file_id + PNG_EXTENSION)

    return {"file_id": file_id, "extension": PNG_EXTENSION}


def build_file_path(file, file_name_suffix=""):
    return MLAI_RESOURCES_DIR + file["file_id"] + file_name_suffix + file["extension"]
