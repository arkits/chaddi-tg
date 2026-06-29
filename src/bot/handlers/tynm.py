import math
import os
import random
import textwrap
import traceback
from dataclasses import dataclass
from datetime import datetime
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

POSTER_SIZE = 1280
POSTER_WIDTH = POSTER_SIZE
POSTER_HEIGHT = POSTER_SIZE
BANNER_HEIGHT = 150
SAFFRON = (255, 140, 0)
SAFFRON_DARK = (204, 85, 0)
SAFFRON_DEEP = (160, 55, 0)
GOLD = (255, 215, 0)
GOLD_LIGHT = (255, 236, 130)
WHITE = (255, 255, 255)
DARK_BROWN = (45, 25, 0)
BJP_GREEN = (19, 136, 8)
FONT_META = "Merriweather-Regular.ttf"
FONT_POOL_GREETING = [
    "Samarkan.ttf",
    "Italianno-Regular.ttf",
    "Cinzel-VariableFont_wght.ttf",
]
FONT_POOL_SUBGREETING = [
    "HomemadeApple-Regular.ttf",
    "Kalam-Regular.ttf",
    "Italianno-Regular.ttf",
]
FONT_POOL_CAPTION = [
    "BebasNeue-Regular.ttf",
    "Cinzel-VariableFont_wght.ttf",
    "OldStandardTT-Bold.ttf",
    "LibreBaskerville-Bold.ttf",
    "Samarkan.ttf",
]
FONT_POOL_BANNER = [
    "Samarkan.ttf",
    "BebasNeue-Regular.ttf",
    "PermanentMarker-Regular.ttf",
]
FONT_POOL_DATE = ["BebasNeue-Regular.ttf", "AmaticSC-Regular.ttf"]


@dataclass(frozen=True)
class PosterLayout:
    name: str
    modi_location: str
    modi_scale: float
    watermark_position: tuple[int, int]
    watermark_size: tuple[int, int]
    watermark_opacity: float
    portrait_corner: str
    portrait_size: int


POSTER_LAYOUTS = [
    PosterLayout(
        name="classic_left",
        modi_location="bottom_left",
        modi_scale=2.1,
        watermark_position=(-60, -30),
        watermark_size=(560, 560),
        watermark_opacity=0.22,
        portrait_corner="bottom_right",
        portrait_size=200,
    ),
    PosterLayout(
        name="right_honour",
        modi_location="bottom_right",
        modi_scale=2.0,
        watermark_position=(780, -20),
        watermark_size=(540, 540),
        watermark_opacity=0.2,
        portrait_corner="bottom_left",
        portrait_size=185,
    ),
    PosterLayout(
        name="top_salute",
        modi_location="top_right",
        modi_scale=2.35,
        watermark_position=(700, 40),
        watermark_size=(500, 500),
        watermark_opacity=0.18,
        portrait_corner="bottom_left",
        portrait_size=190,
    ),
    PosterLayout(
        name="left_tower",
        modi_location="top_left",
        modi_scale=2.25,
        watermark_position=(-80, 20),
        watermark_size=(520, 520),
        watermark_opacity=0.2,
        portrait_corner="bottom_right",
        portrait_size=195,
    ),
    PosterLayout(
        name="center_presence",
        modi_location="center",
        modi_scale=3.1,
        watermark_position=(180, 120),
        watermark_size=(720, 720),
        watermark_opacity=0.14,
        portrait_corner="bottom_right",
        portrait_size=180,
    ),
]

MESSAGE_BOX_MARGIN_X = 120
MESSAGE_BOX_TOP = 300


def extract_reply_text(reply_message) -> str | None:
    if reply_message.text:
        return reply_message.text
    if reply_message.caption:
        return reply_message.caption
    return None


def measure_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("tynm", update)

        if update.message.reply_to_message is None:
            await update.message.reply_text("Please reply to a message with `/tynm`")
            return

        # Load NM_IMG from local resources folder
        nm_img = None
        nm_img_alt = None
        try:
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

            selected_files = pick_distinct_tynm_images(image_files, 2)
            nm_img = Image.open(path.join(TYNM_IMAGES_DIR, selected_files[0]))
            nm_img_alt = Image.open(path.join(TYNM_IMAGES_DIR, selected_files[1]))
            logger.info(
                "Successfully loaded NM_IMG from {} and {}",
                selected_files[0],
                selected_files[1],
            )

        except Exception as e:
            logger.error(
                "Failed to load NM_IMG from local resources: {} traceback={}",
                e,
                traceback.format_exc(),
            )
            await update.message.reply_text("Failed to load image. Please try again later.")
            return

        reply_message = update.message.reply_to_message
        reply_text = extract_reply_text(reply_message)

        # Handle photo message
        if getattr(reply_message, "photo", None):
            try:
                file = await acquire_file(update, context)

                src_img = Image.open(build_file_path(file))
                src_img_width, src_img_height = src_img.size
                logger.debug("src_img_width={} src_img_height={}", src_img_width, src_img_height)

                # Add fancy border and text
                src_img = add_fancy_border(src_img)
                src_img = add_thank_you_text(src_img)

                # Place NM_IMG on the left like the poster layout
                layout = choose_poster_layout()
                img = apply_modi_layout(
                    src_img.convert("RGBA"),
                    nm_img,
                    nm_img_alt,
                    layout,
                )

                # Add decorative elements in corners only
                img = add_poster_decorations(img)

                img.save(build_file_path(file, "_tynm"))

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

        # Handle text or captioned reply (e.g. reply to a URL or message with /tynm)
        elif reply_text:
            unsplash_photo_path = None

            try:
                img, unsplash_photo_path = await compose_text_reply_poster(
                    reply_message,
                    context,
                    reply_text,
                    nm_img,
                    nm_img_alt,
                )
            except Exception as e:
                logger.error(
                    "Caught error in text reply poster composition. e={} traceback={}",
                    e,
                    traceback.format_exc(),
                )
                await update.message.reply_text("Failed to generate image. Please try again.")
                if unsplash_photo_path:
                    util.delete_file(unsplash_photo_path)
                return

            filename = f"{update.message.chat.id}-{update.message.message_id}"
            img_path = path.join(EXTERNAL_DIR, filename + PNG_EXTENSION)
            img.save(img_path)

            with open(img_path, "rb") as photo_to_upload:
                logger.info("[tynm] uploading completed photo")
                await update.message.reply_photo(
                    photo=photo_to_upload,
                )

            util.delete_file(img_path)
            if unsplash_photo_path:
                util.delete_file(unsplash_photo_path)

        else:
            await update.message.reply_text(
                "Please reply to a photo or text message with `/tynm`",
            )

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


def pick_distinct_tynm_images(image_files: list[str], count: int = 2) -> list[str]:
    if len(image_files) >= count:
        return random.sample(image_files, count)

    chosen = image_files[0]
    return [chosen] * count


def pick_font(candidates: list[str]) -> str:
    return random.choice(candidates)


def load_font_from_pool(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    return load_font(pick_font(candidates), size)


def choose_poster_layout() -> PosterLayout:
    layout = random.choice(POSTER_LAYOUTS)
    logger.info("Selected poster layout={}", layout.name)
    return layout


def apply_modi_layout(
    img: Image.Image,
    foreground_modi: Image.Image,
    watermark_modi: Image.Image,
    layout: PosterLayout,
) -> Image.Image:
    foreground = (
        foreground_modi.convert("RGBA")
        if foreground_modi.mode != "RGBA"
        else foreground_modi.copy()
    )
    watermark_source = (
        watermark_modi.convert("RGBA") if watermark_modi.mode != "RGBA" else watermark_modi.copy()
    )

    watermark = ImageOps.contain(watermark_source, layout.watermark_size, Image.LANCZOS)
    paste_with_opacity(img, watermark, layout.watermark_position, layout.watermark_opacity)

    return place_image(img, foreground, scale=layout.modi_scale, location=layout.modi_location)


def paste_framed_portrait(
    img: Image.Image,
    portrait: Image.Image,
    layout: PosterLayout,
    content_height: int,
) -> None:
    framed_portrait = make_circular_portrait(portrait, layout.portrait_size)
    margin = 35

    if layout.portrait_corner == "bottom_right":
        portrait_x = POSTER_WIDTH - framed_portrait.width - margin
        portrait_y = content_height - framed_portrait.height + 10
    elif layout.portrait_corner == "bottom_left":
        portrait_x = margin
        portrait_y = content_height - framed_portrait.height + 10
    else:
        portrait_x = POSTER_WIDTH - framed_portrait.width - margin
        portrait_y = margin

    img.paste(framed_portrait, (portrait_x, portrait_y), framed_portrait)


def load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    for base_dir in (FONTS_DIR, path.join("src", FONTS_DIR)):
        font_path = path.join(base_dir, font_name)
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)

    raise FileNotFoundError(f"Font not found: {font_name}")


def create_saffron_gradient(width: int, height: int) -> Image.Image:
    gradient = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(gradient)
    top_color = (255, 153, 51)
    mid_color = (120, 145, 35)
    bottom_color = BJP_GREEN

    for y in range(height):
        ratio = y / max(height - 1, 1)
        if ratio < 0.5:
            blend = ratio / 0.5
            color = tuple(int(top_color[i] * (1 - blend) + mid_color[i] * blend) for i in range(3))
        else:
            blend = (ratio - 0.5) / 0.5
            color = tuple(
                int(mid_color[i] * (1 - blend) + bottom_color[i] * blend) for i in range(3)
            )
        draw.line([(0, y), (width, y)], fill=color)

    return gradient.convert("RGBA")


def add_lotus_watermark(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    spacing_x = 110
    spacing_y = 95

    for x in range(-20, img.width + spacing_x, spacing_x):
        for y in range(-20, img.height + spacing_y, spacing_y):
            cx = x + ((y // spacing_y) % 2) * (spacing_x // 2)
            cy = y
            draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(255, 255, 255, 18))
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                px = cx + int(24 * math.cos(rad))
                py = cy + int(24 * math.sin(rad))
                draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=(255, 255, 255, 12))

    return Image.alpha_composite(img, overlay)


def blend_unsplash_texture(
    base: Image.Image, unsplash_photo_path: str, width: int, height: int
) -> Image.Image:
    unsplash_photo = Image.open(unsplash_photo_path).convert("RGBA").resize((width, height))
    texture = Image.blend(
        Image.new("RGBA", (width, height), (*SAFFRON, 255)),
        unsplash_photo,
        0.35,
    )
    return Image.blend(base, texture, 0.22)


def paste_with_opacity(
    base: Image.Image, overlay: Image.Image, position: tuple[int, int], opacity: float
) -> None:
    layer = overlay.copy().convert("RGBA")
    alpha = layer.split()[3].point(lambda value: int(value * opacity))
    layer.putalpha(alpha)
    base.paste(layer, position, layer)


def draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] = DARK_BROWN,
    outline_width: int = 2,
) -> None:
    x, y = position
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text(position, text, font=font, fill=fill)


def draw_multiline_text_with_outline(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    line_spacing: int = 8,
    outline: tuple[int, int, int] = DARK_BROWN,
    outline_width: int = 2,
) -> int:
    x, y = position
    total_height = 0

    for line in text.strip().split("\n"):
        if not line:
            continue
        draw_text_with_outline(
            draw, (x, y + total_height), line, font, fill, outline, outline_width
        )
        _line_w, line_h = measure_text(draw, line, font)
        total_height += line_h + line_spacing

    return max(total_height - line_spacing, 0)


def measure_multiline_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    line_spacing: int = 10,
) -> tuple[int, int]:
    lines = [line for line in text.strip().split("\n") if line]
    if not lines:
        return 0, 0

    max_width = 0
    total_height = 0
    for index, line in enumerate(lines):
        line_width, line_height = measure_text(draw, line, font)
        max_width = max(max_width, line_width)
        total_height += line_height
        if index < len(lines) - 1:
            total_height += line_spacing

    return max_width, total_height


def draw_centered_text_with_outline(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] = DARK_BROWN,
    outline_width: int = 2,
) -> None:
    text_width, _text_height = measure_text(draw, text, font)
    draw_text_with_outline(
        draw,
        (center_x - text_width // 2, y),
        text,
        font,
        fill,
        outline,
        outline_width,
    )


def draw_centered_multiline_in_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    line_spacing: int = 10,
    outline: tuple[int, int, int] = DARK_BROWN,
    outline_width: int = 2,
) -> None:
    x0, y0, x1, y1 = box
    lines = [line for line in text.strip().split("\n") if line]
    if not lines:
        return

    _total_width, total_height = measure_multiline_text(draw, text, font, line_spacing)
    center_x = (x0 + x1) // 2
    current_y = y0 + max((y1 - y0 - total_height) // 2, 0)

    for line in lines:
        line_width, line_height = measure_text(draw, line, font)
        draw_text_with_outline(
            draw,
            (center_x - line_width // 2, current_y),
            line,
            font,
            fill,
            outline,
            outline_width,
        )
        current_y += line_height + line_spacing


def make_circular_portrait(
    profile_img: Image.Image, size: int, outer_border: int = 6, inner_border: int = 4
) -> Image.Image:
    portrait = profile_img.convert("RGBA")
    portrait = ImageOps.fit(portrait, (size, size), Image.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    circular = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circular.paste(portrait, (0, 0), mask)

    framed_size = size + (outer_border + inner_border) * 2
    framed = Image.new("RGBA", (framed_size, framed_size), (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(framed)
    center = framed_size // 2
    frame_draw.ellipse(
        [
            center - size // 2 - outer_border - inner_border,
            center - size // 2 - outer_border - inner_border,
            center + size // 2 + outer_border + inner_border,
            center + size // 2 + outer_border + inner_border,
        ],
        fill=SAFFRON,
    )
    frame_draw.ellipse(
        [
            center - size // 2 - inner_border,
            center - size // 2 - inner_border,
            center + size // 2 + inner_border,
            center + size // 2 + inner_border,
        ],
        fill=WHITE,
    )
    framed.paste(circular, (outer_border + inner_border, outer_border + inner_border), circular)
    return framed


def draw_lotus_logo(draw: ImageDraw.ImageDraw, center: tuple[int, int], size: int = 42) -> None:
    cx, cy = center
    draw.ellipse([cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2], fill=WHITE)
    draw.ellipse(
        [cx - size // 2 + 4, cy - size // 2 + 4, cx + size // 2 - 4, cy + size // 2 - 4],
        fill=SAFFRON,
    )

    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        px = cx + int(size * 0.55 * math.cos(rad))
        py = cy + int(size * 0.55 * math.sin(rad))
        draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=WHITE, outline=BJP_GREEN, width=1)

    draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=BJP_GREEN)


def draw_date_badge(
    draw: ImageDraw.ImageDraw,
    timestamp: datetime,
    position: tuple[int, int],
) -> None:
    day = timestamp.strftime("%d")
    month = timestamp.strftime("%b").upper()
    x, y = position
    badge_w, badge_h = 72, 72

    draw.rounded_rectangle(
        [x, y, x + badge_w, y + badge_h],
        radius=10,
        fill=WHITE,
        outline=SAFFRON_DARK,
        width=2,
    )
    day_font = load_font_from_pool(FONT_POOL_DATE, 28)
    month_font = load_font(FONT_META, 14)
    draw.text((x + 18, y + 8), day, font=day_font, fill=SAFFRON_DARK)
    draw.text((x + 14, y + 42), month, font=month_font, fill=DARK_BROWN)


def get_poster_caption_font_size(line_count: int) -> int:
    if line_count <= 3:
        return 58
    if line_count <= 6:
        return 44
    if line_count <= 10:
        return 34
    return 28


def add_poster_bottom_banner(
    img: Image.Image,
    username: str,
    timestamp_str: str,
    chat_title: str | None,
) -> Image.Image:
    draw = ImageDraw.Draw(img)
    banner_top = POSTER_HEIGHT - BANNER_HEIGHT

    draw.rectangle([0, banner_top, POSTER_WIDTH, POSTER_HEIGHT], fill=WHITE)
    draw.line([(0, banner_top), (POSTER_WIDTH, banner_top)], fill=SAFFRON_DARK, width=3)

    draw_lotus_logo(draw, (70, banner_top + BANNER_HEIGHT // 2))

    name_font = load_font_from_pool(FONT_POOL_BANNER, 54)
    meta_font = load_font(FONT_META, 22)
    display_name = username.removeprefix("~ ").strip()
    draw.text((130, banner_top + 18), display_name, font=name_font, fill=SAFFRON_DARK)

    meta_lines = [timestamp_str]
    if chat_title:
        meta_lines.append(chat_title)
    meta_y = banner_top + 72
    for line in meta_lines:
        draw.text((132, meta_y), line, font=meta_font, fill=(90, 60, 30))
        meta_y += 26

    return img


def add_poster_decorations(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    img_width, img_height = img.size
    content_height = img_height - BANNER_HEIGHT

    corner_placements = [
        (img_width - 90, 20, 70),
        (img_width - 170, 70, 55),
        (20, content_height - 120, 50),
        (90, content_height - 70, 45),
    ]

    for index, (x, y, size) in enumerate(corner_placements):
        element = draw_firework(size) if index % 2 == 0 else draw_flower(size)
        img.paste(element, (x, y), element)

    return img


async def fetch_user_profile_portrait(
    context: ContextTypes.DEFAULT_TYPE, user
) -> Image.Image | None:
    user_profile_photo_path = path.join(EXTERNAL_DIR, f"{user.id}.webp")

    try:
        user_profile_photos = await user.get_profile_photos(limit=1)
        if not user_profile_photos or not getattr(user_profile_photos, "photos", None):
            return None

        user_profile_photo = user_profile_photos.photos[0]
        if not user_profile_photo:
            return None

        user_profile_photo_file = await context.bot.get_file(user_profile_photo[-1].file_id)
        await user_profile_photo_file.download_to_drive(user_profile_photo_path)
        portrait = Image.open(user_profile_photo_path).convert("RGBA")
        util.delete_file(user_profile_photo_path)
        return portrait
    except Exception as e:
        logger.warning("[tynm] unable to fetch user profile portrait e={}", e)
        util.delete_file(user_profile_photo_path)
        return None


async def compose_text_reply_poster(
    reply_message,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    foreground_modi: Image.Image,
    watermark_modi: Image.Image,
) -> tuple[Image.Image, str | None]:
    unsplash_photo_path = None
    width, height = POSTER_WIDTH, POSTER_HEIGHT
    content_height = height - BANNER_HEIGHT
    layout = choose_poster_layout()

    img = create_saffron_gradient(width, height)
    img = add_lotus_watermark(img)

    try:
        unsplash_photo_path = util.fetch_random_unsplash_photo_path(width, height)
        if unsplash_photo_path:
            img = blend_unsplash_texture(img, unsplash_photo_path, width, height)
    except Exception as e:
        logger.warning(
            "Caught error in unsplash background composition. e={} traceback={}",
            e,
            traceback.format_exc(),
        )

    img = apply_modi_layout(img, foreground_modi, watermark_modi, layout)

    draw = ImageDraw.Draw(img)
    caption = generate_wrapped_caption(text)
    line_count = len([line for line in caption.split("\n") if line.strip()])
    logger.info("number_of_lines={}", line_count)

    greeting_font = load_font_from_pool(FONT_POOL_GREETING, 58)
    caption_font = load_font_from_pool(
        FONT_POOL_CAPTION,
        get_poster_caption_font_size(line_count),
    )
    center_x = width // 2
    greeting_y = 90

    draw_centered_text_with_outline(
        draw,
        center_x,
        greeting_y,
        "thank you modi ji!",
        greeting_font,
        WHITE,
        outline=SAFFRON_DEEP,
        outline_width=3,
    )
    draw_centered_text_with_outline(
        draw,
        center_x,
        greeting_y + 62,
        "heartfelt wishes!",
        load_font_from_pool(FONT_POOL_SUBGREETING, 44),
        GOLD_LIGHT,
        outline=SAFFRON_DEEP,
        outline_width=2,
    )

    message_area = (
        MESSAGE_BOX_MARGIN_X,
        MESSAGE_BOX_TOP,
        width - MESSAGE_BOX_MARGIN_X,
        content_height - 50,
    )
    draw_centered_multiline_in_box(
        draw,
        message_area,
        caption.strip(),
        caption_font,
        GOLD,
        line_spacing=12,
        outline=SAFFRON_DEEP,
        outline_width=3,
    )

    timestamp = util.normalize_datetime(reply_message.date)
    draw_date_badge(draw, timestamp, (width - 110, 30))

    profile_portrait = await fetch_user_profile_portrait(context, reply_message.from_user)
    if profile_portrait is not None:
        paste_framed_portrait(img, profile_portrait, layout, content_height)

    username = "~ " + util.extract_pretty_name_from_tg_user(reply_message.from_user)
    timestamp_str = timestamp.strftime("%d/%m/%Y, %I:%M %p")
    chat_title = reply_message.chat.title if reply_message.chat else None
    img = add_poster_bottom_banner(img, username, timestamp_str, chat_title)
    img = add_poster_decorations(img)

    return img, unsplash_photo_path


def add_fancy_border(img: Image) -> Image:
    """Add a fancy decorative border to the image."""
    border_width = 20
    outer_border_width = 5
    img_width, img_height = img.size

    # Create a new image with border space
    bordered_img = Image.new(
        "RGB", (img_width + 2 * border_width, img_height + 2 * border_width), color=(255, 255, 255)
    )

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
            [
                (outer_border_width - i, outer_border_width - i),
                (
                    img_width + 2 * border_width - outer_border_width + i,
                    img_height + 2 * border_width - outer_border_width + i,
                ),
            ],
            outline=(0, 0, 0),
        )

    # Middle border (medium, orange/saffron)
    for i in range(4):
        draw.rectangle(
            [
                (outer_border_width + 3 - i, outer_border_width + 3 - i),
                (
                    img_width + 2 * border_width - outer_border_width - 3 + i,
                    img_height + 2 * border_width - outer_border_width - 3 + i,
                ),
            ],
            outline=(255, 153, 51),
        )

    # Inner border (thin, white)
    for i in range(2):
        draw.rectangle(
            [
                (outer_border_width + 7 - i, outer_border_width + 7 - i),
                (
                    img_width + 2 * border_width - outer_border_width - 7 + i,
                    img_height + 2 * border_width - outer_border_width - 7 + i,
                ),
            ],
            outline=(255, 255, 255),
        )

    # Decorative corner elements
    corner_size = 15
    corner_thickness = 3

    # Top-left corner
    draw.line(
        [
            (outer_border_width, outer_border_width),
            (outer_border_width + corner_size, outer_border_width),
        ],
        fill=(255, 153, 51),
        width=corner_thickness,
    )
    draw.line(
        [
            (outer_border_width, outer_border_width),
            (outer_border_width, outer_border_width + corner_size),
        ],
        fill=(255, 153, 51),
        width=corner_thickness,
    )

    # Top-right corner
    draw.line(
        [
            (img_width + 2 * border_width - outer_border_width, outer_border_width),
            (img_width + 2 * border_width - outer_border_width - corner_size, outer_border_width),
        ],
        fill=(255, 153, 51),
        width=corner_thickness,
    )
    draw.line(
        [
            (img_width + 2 * border_width - outer_border_width, outer_border_width),
            (img_width + 2 * border_width - outer_border_width, outer_border_width + corner_size),
        ],
        fill=(255, 153, 51),
        width=corner_thickness,
    )

    # Bottom-left corner
    draw.line(
        [
            (outer_border_width, img_height + 2 * border_width - outer_border_width),
            (outer_border_width + corner_size, img_height + 2 * border_width - outer_border_width),
        ],
        fill=(255, 153, 51),
        width=corner_thickness,
    )
    draw.line(
        [
            (outer_border_width, img_height + 2 * border_width - outer_border_width),
            (outer_border_width, img_height + 2 * border_width - outer_border_width - corner_size),
        ],
        fill=(255, 153, 51),
        width=corner_thickness,
    )

    # Bottom-right corner
    draw.line(
        [
            (
                img_width + 2 * border_width - outer_border_width,
                img_height + 2 * border_width - outer_border_width,
            ),
            (
                img_width + 2 * border_width - outer_border_width - corner_size,
                img_height + 2 * border_width - outer_border_width,
            ),
        ],
        fill=(255, 153, 51),
        width=corner_thickness,
    )
    draw.line(
        [
            (
                img_width + 2 * border_width - outer_border_width,
                img_height + 2 * border_width - outer_border_width,
            ),
            (
                img_width + 2 * border_width - outer_border_width,
                img_height + 2 * border_width - outer_border_width - corner_size,
            ),
        ],
        fill=(255, 153, 51),
        width=corner_thickness,
    )

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
        font = load_font_from_pool(FONT_POOL_GREETING, font_size)
    except Exception as e:
        logger.warning("Failed to load poster font, using default. e={}", e)
        font = ImageFont.load_default()

    # Get text dimensions
    text_width, text_height = measure_text(draw, text, font)

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
