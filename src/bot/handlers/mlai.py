import datetime
import traceback
import boto3
from telegram import Update
from telegram.parsemode import ParseMode
from src.domain import dc, util
from loguru import logger
from PIL import Image, ImageDraw, ExifTags, ImageColor

rekognition_client = boto3.client("rekognition")

MLAI_RESOURCE_DIR = "resources/mlai/"
JPG_EXTENSION = ".jpg"


def handle(update: Update, context):

    try:

        # Count time taken
        time_start = datetime.datetime.now()

        dc.log_command_usage("mlai", update)

        reply_text = """
*chaddi-ai analysis \n*
"""

        # Extract file ID from update
        file_id = update.message.reply_to_message.photo[-1].file_id

        logger.info("[mlai] Starting file download file_id={}", file_id)
        file_handle = context.bot.get_file(file_id)
        file_handle.download(MLAI_RESOURCE_DIR + str(file_id) + JPG_EXTENSION)

        logger.info("[mlai] Running rekognition on file_id={}", file_id)
        with open(MLAI_RESOURCE_DIR + str(file_id) + JPG_EXTENSION, "rb") as photo_file:
            response = rekognition_client.detect_faces(
                Image={"Bytes": photo_file.read()}, Attributes=["ALL"]
            )

        logger.debug("[mlai] response={}", response)

        # Draw bounding boxes on the image
        image = Image.open(MLAI_RESOURCE_DIR + str(file_id) + JPG_EXTENSION)
        img_width, img_height = image.size
        draw = ImageDraw.Draw(image)

        reply_text += "*Facial Analysis* \n"
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
                face_detail["Emotions"][0]["Type"],
            )

            box = face_detail["BoundingBox"]
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

        image.save(MLAI_RESOURCE_DIR + str(file_id) + "_mlai" + JPG_EXTENSION)

        with open(
            MLAI_RESOURCE_DIR + str(file_id) + "_mlai" + JPG_EXTENSION, "rb"
        ) as photo_to_upload:
            update.message.reply_photo(
                photo=photo_to_upload,
                caption=reply_text,
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as e:
        logger.error(
            "Caught Error in mlai.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
