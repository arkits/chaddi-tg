import math
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
TYNM_IMAGES_DIR = path.join(util.RESOURCES_DIR, "tynm")
PNG_EXTENSION = ".png"
NM_IMG_LOCATIONS = ["bottom_right", "bottom_left", "top_right", "top_left", "center"]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("tynm", update)

        if update.message.reply_to_message is None:
            await update.message.reply_text("Please reply to a message with `/tynm`")
            return

        # Load NM_IMG from local resources folder
        nm_img = None
        try:
            # Get all image files from tynm directory
            if not os.path.exists(TYNM_IMAGES_DIR):
                logger.error("TYNM images directory does not exist: {}", TYNM_IMAGES_DIR)
                await update.message.reply_text("TYNM images not found. Please contact admin.")
                return

            image_files = [
                f
                for f in os.listdir(TYNM_IMAGES_DIR)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
            ]

            if not image_files:
                logger.error("No image files found in TYNM directory: {}", TYNM_IMAGES_DIR)
                await update.message.reply_text("No TYNM images available. Please contact admin.")
                return

            # Randomly select an image file
            selected_image = util.choose_random_element_from_list(image_files)
            image_path = path.join(TYNM_IMAGES_DIR, selected_image)

            logger.debug("Loading NM_IMG from local file: {}", image_path)

            # Load and validate the image
            nm_img = Image.open(image_path)
            logger.info("Successfully loaded NM_IMG from {}", selected_image)

        except Exception as e:
            logger.error("Failed to load NM_IMG from local resources: {} traceback={}", e, traceback.format_exc())
            await update.message.reply_text("Failed to load image. Please try again later.")
            return

        # Handle photo message
        if getattr(update.message.reply_to_message, "photo", None):
            try:
                file = await acquire_file(update, context)

                src_img = Image.open(build_file_path(file))
                src_img_width, src_img_height = src_img.size
                logger.debug("src_img_width={} src_img_height={}", src_img_width, src_img_height)

                # Add fancy border and text
                src_img = add_fancy_border(src_img)
                src_img = add_thank_you_text(src_img)

                # Place NM_IMG with random location and scale
                nm_img_location = random.choice(NM_IMG_LOCATIONS)
                nm_img_scale = random.uniform(1.5, 3.0)
                logger.info("nm_img_location={} nm_img_scale={:.2f}", nm_img_location, nm_img_scale)
                src_img = place_image(src_img, nm_img, location=nm_img_location, scale=nm_img_scale)

                # Add decorative fireworks and flowers
                src_img = add_decorative_elements(src_img)

                src_img.save(build_file_path(file, "_tynm"))

                with open(build_file_path(file, "_tynm"), "rb") as photo_to_upload:
                    logger.info("[tynm] uploading completed photo")
                    await update.message.reply_photo(
                        photo=photo_to_upload,
                    )

                util.delete_file(build_file_path(file))
                util.delete_file(build_file_path(file, "_tynm"))

            except Exception as e:
                logger.error(
                    "Caught error in photo message handling. e={} traceback={}",
                    e,
                    traceback.format_exc(),
                )
                await update.message.reply_text("Failed to process photo. Please try again.")

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

                if not user_profile_photos or not getattr(user_profile_photos, "photos", None):
                    raise ValueError("No profile photo available for the user")

                user_profile_photo = user_profile_photos.photos[0]
                if not user_profile_photo:
                    raise ValueError("No profile photo available for the user")

                # pick highest resolution
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

            # nm_image composition with random location and scale
            nm_img_location = random.choice(NM_IMG_LOCATIONS)
            nm_img_scale = random.uniform(1.5, 3.0)
            logger.info("nm_img_location={} nm_img_scale={:.2f}", nm_img_location, nm_img_scale)
            img = place_image(
                img,
                nm_img,
                location=nm_img_location,
                scale=nm_img_scale,
            )

            # Add decorative fireworks and flowers
            img = add_decorative_elements(img)

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


def add_fancy_border(img: Image) -> Image:
    """Add a fancy decorative border to the image."""
    border_width = 20
    outer_border_width = 5
    img_width, img_height = img.size

    # Create a new image with border space
    bordered_img = Image.new("RGB", (img_width + 2 * border_width, img_height + 2 * border_width), color=(255, 255, 255))

    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Paste original image in the center
    bordered_img.paste(img, (border_width, border_width))

    # Draw decorative borders
    draw = ImageDraw.Draw(bordered_img)

    # Outer border (thick, dark) - draw multiple rectangles for thickness
    for i in range(outer_border_width):
        draw.rectangle(
            [(outer_border_width - i, outer_border_width - i), (img_width + 2 * border_width - outer_border_width + i, img_height + 2 * border_width - outer_border_width + i)],
            outline=(0, 0, 0),
        )

    # Middle border (medium, orange/saffron)
    for i in range(4):
        draw.rectangle(
            [(outer_border_width + 3 - i, outer_border_width + 3 - i), (img_width + 2 * border_width - outer_border_width - 3 + i, img_height + 2 * border_width - outer_border_width - 3 + i)],
            outline=(255, 153, 51),
        )

    # Inner border (thin, white)
    for i in range(2):
        draw.rectangle(
            [(outer_border_width + 7 - i, outer_border_width + 7 - i), (img_width + 2 * border_width - outer_border_width - 7 + i, img_height + 2 * border_width - outer_border_width - 7 + i)],
            outline=(255, 255, 255),
        )

    # Decorative corner elements
    corner_size = 15
    corner_thickness = 3

    # Top-left corner
    draw.line([(outer_border_width, outer_border_width), (outer_border_width + corner_size, outer_border_width)], fill=(255, 153, 51), width=corner_thickness)
    draw.line([(outer_border_width, outer_border_width), (outer_border_width, outer_border_width + corner_size)], fill=(255, 153, 51), width=corner_thickness)

    # Top-right corner
    draw.line([(img_width + 2 * border_width - outer_border_width, outer_border_width), (img_width + 2 * border_width - outer_border_width - corner_size, outer_border_width)], fill=(255, 153, 51), width=corner_thickness)
    draw.line([(img_width + 2 * border_width - outer_border_width, outer_border_width), (img_width + 2 * border_width - outer_border_width, outer_border_width + corner_size)], fill=(255, 153, 51), width=corner_thickness)

    # Bottom-left corner
    draw.line([(outer_border_width, img_height + 2 * border_width - outer_border_width), (outer_border_width + corner_size, img_height + 2 * border_width - outer_border_width)], fill=(255, 153, 51), width=corner_thickness)
    draw.line([(outer_border_width, img_height + 2 * border_width - outer_border_width), (outer_border_width, img_height + 2 * border_width - outer_border_width - corner_size)], fill=(255, 153, 51), width=corner_thickness)

    # Bottom-right corner
    draw.line([(img_width + 2 * border_width - outer_border_width, img_height + 2 * border_width - outer_border_width), (img_width + 2 * border_width - outer_border_width - corner_size, img_height + 2 * border_width - outer_border_width)], fill=(255, 153, 51), width=corner_thickness)
    draw.line([(img_width + 2 * border_width - outer_border_width, img_height + 2 * border_width - outer_border_width), (img_width + 2 * border_width - outer_border_width, img_height + 2 * border_width - outer_border_width - corner_size)], fill=(255, 153, 51), width=corner_thickness)

    return bordered_img


def add_thank_you_text(img: Image) -> Image:
    """Add 'thank you modi ji!' text to the image."""
    draw = ImageDraw.Draw(img)
    img_width, img_height = img.size

    # Text to display
    text = "thank you modi ji!"

    # Try to use a font from the fonts directory, fallback to default
    font_size = max(40, int(img_width / 20))
    try:
        if os.path.exists(FONTS_DIR) and os.listdir(FONTS_DIR):
            random_font = util.choose_random_element_from_list(os.listdir(FONTS_DIR))
            font_path = path.join(FONTS_DIR, random_font)
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except Exception as e:
        logger.warning("Failed to load custom font, using default. e={}", e)
        font = ImageFont.load_default()

    # Get text dimensions
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older PIL versions
        text_width, text_height = draw.textsize(text, font=font)

    # Position text at bottom center with padding
    text_x = (img_width - text_width) // 2
    text_y = img_height - text_height - 30

    # Draw text with outline (shadow effect)
    outline_width = 3
    for adj in range(-outline_width, outline_width + 1):
        for adj2 in range(-outline_width, outline_width + 1):
            if adj != 0 or adj2 != 0:
                draw.text(
                    (text_x + adj, text_y + adj2),
                    text,
                    font=font,
                    fill=(0, 0, 0),
                )

    # Draw main text in saffron/orange color
    draw.text((text_x, text_y), text, font=font, fill=(255, 153, 51))

    return img


def draw_firework(size: int = 60) -> Image:
    """Draw a colorful firework clipart."""
    # Create transparent image
    firework = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(firework)

    center_x, center_y = size // 2, size // 2

    # Firework colors (bright and festive)
    colors = [
        (255, 215, 0),  # Gold
        (255, 20, 147),  # Deep pink
        (0, 191, 255),  # Deep sky blue
        (255, 140, 0),  # Dark orange
        (50, 205, 50),  # Lime green
    ]

    # Draw radiating lines (sparks)
    num_sparks = 12
    spark_length = size // 2 - 5

    for i in range(num_sparks):
        angle = (2 * math.pi * i) / num_sparks
        color = random.choice(colors)

        # Calculate end point using trigonometry
        end_x = center_x + int(spark_length * math.cos(angle))
        end_y = center_y + int(spark_length * math.sin(angle))

        # Draw main spark line
        draw.line([(center_x, center_y), (end_x, end_y)], fill=color, width=3)

        # Add small circles at the end (sparkle effect)
        draw.ellipse([end_x - 3, end_y - 3, end_x + 3, end_y + 3], fill=color)

    # Draw center circle
    draw.ellipse([center_x - 5, center_y - 5, center_x + 5, center_y + 5], fill=(255, 255, 0))

    return firework


def draw_flower(size: int = 50) -> Image:
    """Draw a decorative flower clipart."""
    # Create transparent image
    flower = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(flower)

    center_x, center_y = size // 2, size // 2

    # Flower colors (bright and cheerful)
    petal_colors = [
        (255, 192, 203),  # Pink
        (255, 20, 147),  # Deep pink
        (255, 165, 0),  # Orange
        (255, 215, 0),  # Gold
        (255, 105, 180),  # Hot pink
    ]

    petal_color = random.choice(petal_colors)
    center_color = (255, 215, 0)  # Gold center

    # Draw petals (5 petals for a simple flower)
    num_petals = 5
    petal_radius = size // 3

    for i in range(num_petals):
        angle = (2 * math.pi * i) / num_petals
        # Calculate petal position using trigonometry
        petal_x = center_x + int(petal_radius * math.cos(angle))
        petal_y = center_y + int(petal_radius * math.sin(angle))

        # Draw petal as ellipse
        petal_size = size // 4
        draw.ellipse(
            [
                petal_x - petal_size // 2,
                petal_y - petal_size // 2,
                petal_x + petal_size // 2,
                petal_y + petal_size // 2,
            ],
            fill=petal_color,
            outline=(255, 255, 255),
            width=1,
        )

    # Draw center circle
    center_radius = size // 6
    draw.ellipse(
        [
            center_x - center_radius,
            center_y - center_radius,
            center_x + center_radius,
            center_y + center_radius,
        ],
        fill=center_color,
        outline=(255, 140, 0),
        width=2,
    )

    return flower


def add_decorative_elements(img: Image) -> Image:
    """Add fireworks and flowers as decorative elements to the image."""
    # Ensure image is RGBA
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    img_width, img_height = img.size

    # Number of decorative elements (fireworks and flowers)
    num_fireworks = random.randint(2, 4)
    num_flowers = random.randint(3, 6)

    # Add fireworks (typically at top corners and edges)
    for _ in range(num_fireworks):
        firework_size = random.randint(40, 80)
        firework = draw_firework(firework_size)

        # Random position (prefer top area and corners)
        if random.random() > 0.5:
            # Top area
            x = random.randint(20, img_width - firework_size - 20)
            y = random.randint(20, img_height // 3)
        else:
            # Random edge
            side = random.choice(["top", "left", "right"])
            if side == "top":
                x = random.randint(20, img_width - firework_size - 20)
                y = random.randint(10, 50)
            elif side == "left":
                x = random.randint(10, 50)
                y = random.randint(20, img_height - firework_size - 20)
            else:  # right
                x = img_width - firework_size - random.randint(10, 50)
                y = random.randint(20, img_height - firework_size - 20)

        # Paste firework with transparency
        img.paste(firework, (x, y), firework)

    # Add flowers (scattered around, prefer corners and edges)
    for _ in range(num_flowers):
        flower_size = random.randint(30, 60)
        flower = draw_flower(flower_size)

        # Random position (prefer corners and edges)
        if random.random() > 0.3:
            # Corners
            corner = random.choice(["top_left", "top_right", "bottom_left", "bottom_right"])
            if corner == "top_left":
                x = random.randint(10, 80)
                y = random.randint(10, 80)
            elif corner == "top_right":
                x = img_width - flower_size - random.randint(10, 80)
                y = random.randint(10, 80)
            elif corner == "bottom_left":
                x = random.randint(10, 80)
                y = img_height - flower_size - random.randint(10, 80)
            else:  # bottom_right
                x = img_width - flower_size - random.randint(10, 80)
                y = img_height - flower_size - random.randint(10, 80)
        else:
            # Random position
            x = random.randint(20, img_width - flower_size - 20)
            y = random.randint(20, img_height - flower_size - 20)

        # Paste flower with transparency
        img.paste(flower, (x, y), flower)

    logger.info("Added {} fireworks and {} flowers to image", num_fireworks, num_flowers)
    return img


def place_image(src_img: Image, placement_img: Image, scale=2, location="bottom_right") -> Image:
    # Convert placement_img to RGBA to preserve transparency
    if placement_img.mode != "RGBA":
        placement_img = placement_img.convert("RGBA")

    # Ensure src_img is RGBA to support transparency
    if src_img.mode != "RGBA":
        src_img = src_img.convert("RGBA")

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
        Image.LANCZOS,
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
            (src_img_width - placement_img_width, src_img_height - placement_img_height),
            placement_img,
        )

    elif location == "bottom_left":
        placement_img = ImageOps.mirror(placement_img)

        src_img.paste(
            placement_img,
            (0, src_img_height - placement_img_height),
            placement_img,
        )

    elif location == "top_right":
        src_img.paste(
            placement_img,
            (src_img_width - placement_img_width, 0),
            placement_img,
        )

    elif location == "top_left":
        placement_img = ImageOps.mirror(placement_img)

        src_img.paste(
            placement_img,
            (0, 0),
            placement_img,
        )

    elif location == "center":
        src_img.paste(
            placement_img,
            (
                (src_img_width - placement_img_width) // 2,
                (src_img_height - placement_img_height) // 2,
            ),
            placement_img,
        )

    return src_img


async def acquire_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Extract file ID from update
    file_id = str(update.message.reply_to_message.photo[-1].file_id)  # TODO: handle video and gifs?

    logger.info("[tynm] Starting file download file_id={}", file_id)
    file_handle = await context.bot.get_file(file_id)
    await file_handle.download_to_drive(MLAI_RESOURCES_DIR + file_id + PNG_EXTENSION)

    return {"file_id": file_id, "extension": PNG_EXTENSION}


def build_file_path(file, file_name_suffix=""):
    return MLAI_RESOURCES_DIR + file["file_id"] + file_name_suffix + file["extension"]
