from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import textwrap
import requests
from loguru import logger
from util import util
import ciso8601


QUOTE_PICS_RESOURCES_DIR = "resources/quote_pics/"
JPEG_EXTENSION = ".jpeg"

FONT_CAPTION_86 = ImageFont.truetype("resources/fonts/Kalam-Regular.ttf", 86)
FONT_CAPTION_64 = ImageFont.truetype("resources/fonts/Kalam-Regular.ttf", 64)
FONT_AUTHOR = ImageFont.truetype("resources/fonts/Montserrat-Medium.ttf", 50)
FONT_DATE = ImageFont.truetype("resources/fonts/Montserrat-Medium.ttf", 32)

PADDING_PX = 20


def generate_quote_pic(quote, update):

    quote_id = str(quote["id"])
    quote_caption = '"' + sanitize_quote_message(quote["message"][0]["message"]) + '"'
    quote_author = "- " + quote["user"]
    quote_date = generate_pretty_quote_date(quote["date"])

    download_background_picture(quote_id)

    img = Image.open(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION)
    img = img.convert("RGBA")
    img = img.resize((1920, 1080))
    img_width, img_height = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 180))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    draw = add_quote_caption(draw, quote_caption, img_width, img_height)

    draw, e_height = add_quote_date(draw, quote_date, img_width, img_height)

    draw = add_quote_author(draw, quote_author, img_width, img_height, e_height)

    img = img.convert("RGB")
    img.save(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION)

    logger.info("[quote-pics] Uploading result")
    update.message.reply_photo(
        photo=open(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION, "rb"),
        timeout=5000,
    )

    util.delete_file(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION)

    return


def download_background_picture(quote_id):

    logger.info("[quote-pics] Downloading background picture")

    url = "https://source.unsplash.com/collection/898543/"

    r = requests.get(url, allow_redirects=True)

    open(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION, "wb").write(r.content)

    logger.info("[quote-pics] Finished downloading background picture")

    return


def sanitize_quote_message(message):

    if isinstance(message, (bytes, bytearray)):
        return str(message, "utf-8")
    else:
        if message.startswith("b'") or message.startswith('b"'):
            trimed = message[2:-1]
            return trimed

    return message


def generate_wrapped_caption(quote_caption):

    caption_new = ""

    wrapper = textwrap.TextWrapper(width=40)
    word_list = wrapper.wrap(text=quote_caption)

    for ii in word_list[:-1]:
        caption_new = caption_new + ii + "\n"

    caption_new += word_list[-1]

    return caption_new


def add_quote_caption(draw, quote_caption, img_width, img_height):

    wrapped_caption = generate_wrapped_caption(quote_caption)

    if len(quote_caption) < 350:
        font_to_use = FONT_CAPTION_86
    else:
        font_to_use = FONT_CAPTION_64

    caption_width, caption_height = draw.textsize(wrapped_caption, font=font_to_use)

    caption_x, caption_y = (
        0.5 * (img_width - caption_width),
        0.5 * img_height - caption_height,
    )

    if caption_x < 0:
        caption_x = 0

    if caption_y < 0:
        caption_y = PADDING_PX

    draw.text(
        (caption_x, caption_y), wrapped_caption, fill="white", font=font_to_use,
    )

    return draw


def add_quote_author(draw, quote_author, img_width, img_height, e_height):

    subtitle_text_width, subtitle_text_height = draw.textsize(
        quote_author, font=FONT_AUTHOR
    )

    x = (img_width - subtitle_text_width) / 2

    y = img_height - (subtitle_text_height + e_height + PADDING_PX)

    draw.text(
        (x, y), quote_author, fill="white", font=FONT_AUTHOR, align="center",
    )

    return draw


def add_quote_date(draw, quote_date, img_width, img_height):

    subtitle_text_width, subtitle_text_height = draw.textsize(
        quote_date, font=FONT_DATE
    )

    x = (img_width - subtitle_text_width) / 2

    y = img_height - (subtitle_text_height + PADDING_PX)

    draw.text(
        (x, y), quote_date, fill="white", font=FONT_DATE, align="center",
    )

    return draw, subtitle_text_height


def generate_pretty_quote_date(quote_date):

    pretty_date = ""

    d = ciso8601.parse_datetime(quote_date)

    pretty_date = d.strftime("%d %B %Y")

    return pretty_date
