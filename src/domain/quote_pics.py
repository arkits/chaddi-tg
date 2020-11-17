from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import textwrap
import requests
from loguru import logger


QUOTE_PICS_RESOURCES_DIR = "resources/quote_pics/"
JPEG_EXTENSION = ".jpeg"

FONT_CAPTION = ImageFont.truetype("resources/fonts/Kalam-Regular.ttf", 86)
FONT_AUTHOR = ImageFont.truetype("resources/fonts/Montserrat-Medium.ttf", 50)


def generate_quote_pic(quote, update):

    quote_id = str(quote["id"])
    quote_caption = '"' + sanitize_quote_message(quote["message"][0]["message"]) + '"'
    quote_author = "- " + quote["user"]
    quote_date = quote["date"]

    download_background_picture(quote_id)

    img = Image.open(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION)
    img = img.convert("RGBA")
    img = img.resize((1920, 1080))
    img_width, img_height = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 200))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    draw, caption_height = add_quote_caption(draw, quote_caption, img_width, img_height)

    draw = add_quote_author(draw, quote_author, caption_height, img_width)

    img = img.convert("RGB")
    img.save(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION)

    logger.info("[quote-pics] uploading result")
    update.message.reply_photo(
        photo=open(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION, "rb"),
        timeout=5000,
    )

    return


def download_background_picture(quote_id):

    logger.info("[quote-pics] downloading file")

    url = "https://source.unsplash.com/collection/190727/"

    r = requests.get(url, allow_redirects=True)

    open(QUOTE_PICS_RESOURCES_DIR + quote_id + JPEG_EXTENSION, "wb").write(r.content)

    logger.info("[quote-pics] finished downloading file")

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

    wrapper = textwrap.TextWrapper(width=50)
    word_list = wrapper.wrap(text=quote_caption)

    for ii in word_list[:-1]:
        caption_new = caption_new + ii + "\n"

    caption_new += word_list[-1]

    return caption_new


def add_quote_caption(draw, quote_caption, img_width, img_height):

    wrapped_caption = generate_wrapped_caption(quote_caption)

    caption_width, caption_height = draw.textsize(wrapped_caption, font=FONT_CAPTION)

    caption_x, caption_y = (
        0.5 * (img_width - caption_width),
        0.5 * img_height - caption_height,
    )

    if caption_x < 0:
        caption_x = 0

    if caption_y < 0:
        caption_y = 10

    draw.text(
        (caption_x, caption_y), wrapped_caption, fill="white", font=FONT_CAPTION,
    )

    return draw, caption_height


def add_quote_author(draw, quote_author, caption_height, img_width):

    subtitle = quote_author

    subtitle_text_width, subtitle_text_height = draw.textsize(
        subtitle, font=FONT_AUTHOR
    )

    draw.text(
        ((img_width - subtitle_text_width) / 2, caption_height + 10),
        subtitle,
        fill="white",
        font=FONT_AUTHOR,
        align="center",
    )

    return draw
