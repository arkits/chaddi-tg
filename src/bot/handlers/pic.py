import os
import shutil
import tempfile
import traceback

import requests
from ddgs import DDGS
from loguru import logger
from telegram import InputMediaPhoto, Update
from telegram.ext import ContextTypes

from src.domain import config, dc

app_config = config.get_config()


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("pic", update)

        # Extract search query from message
        search_query = None

        # Check for text in command args
        if context.args:
            search_query = " ".join(context.args)

        # Check for reply to message
        if not search_query and update.message.reply_to_message:
            reply_message = update.message.reply_to_message
            if reply_message.text:
                search_query = reply_message.text
            elif reply_message.caption:
                search_query = reply_message.caption

        # Check for caption in current message
        if not search_query and update.message.caption:
            caption = update.message.caption
            search_query = caption[4:].strip() if caption.startswith("/pic") else caption

        if not search_query or search_query.strip() == "":
            await update.message.reply_text(
                "Please provide a search query. Usage: `/pic <search term>` or reply to a message with `/pic`.",
                parse_mode="Markdown",
            )
            return

        search_query = search_query.strip()
        logger.info(f"[pic] search_query={search_query}")

        # Send initial message
        sent_message = await update.message.reply_text("Searching for images...")

        # Create temporary directory for downloads
        temp_dir = tempfile.mkdtemp(prefix="pic_")
        download_dir = os.path.join(temp_dir, "downloads")
        os.makedirs(download_dir, exist_ok=True)

        try:
            # Search for images using DuckDuckGo
            ddgs = DDGS()
            # Search for images
            results = list(ddgs.images(
                query=search_query,
                max_results=5,
                safesearch="on"
            ))

            if len(results) == 0:
                await sent_message.edit_text("No images found for your search query.")
                return

            # Download images
            downloaded_files = []
            for idx, result in enumerate(results[:5]):
                try:
                    image_url = result.get("image")
                    if not image_url:
                        continue

                    # Download image
                    response = requests.get(image_url, timeout=10, allow_redirects=True)
                    response.raise_for_status()

                    # Determine file extension from content type or URL
                    content_type = response.headers.get("content-type", "")
                    if "jpeg" in content_type or "jpg" in content_type:
                        ext = ".jpg"
                    elif "png" in content_type:
                        ext = ".png"
                    elif "gif" in content_type:
                        ext = ".gif"
                    elif "webp" in content_type:
                        ext = ".webp"
                    else:
                        # Try to infer from URL
                        ext = os.path.splitext(image_url.split("?")[0])[1]
                        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                            ext = ".jpg"  # Default to jpg

                    # Save image
                    image_path = os.path.join(download_dir, f"image_{idx}{ext}")
                    with open(image_path, "wb") as f:
                        f.write(response.content)

                    downloaded_files.append(image_path)
                    logger.info(f"[pic] Downloaded image {idx+1}/5: {image_url[:50]}...")

                except Exception as e:
                    logger.warning(f"[pic] Error downloading image {idx+1}: {e}")
                    continue

            if len(downloaded_files) == 0:
                await sent_message.edit_text("No images found for your search query.")
                return

            # Limit to 5 images
            downloaded_files = downloaded_files[:5]

            logger.info(f"[pic] downloaded {len(downloaded_files)} images")

            # Upload individual images as a media group
            await sent_message.edit_text("Uploading images...")
            if len(downloaded_files) > 0:
                # Telegram allows up to 10 media in a group, so we can send all 5
                # Open files and create media list
                media_list = []
                file_handles = []
                try:
                    for img_path in downloaded_files:
                        file_handle = open(img_path, "rb")
                        file_handles.append(file_handle)
                        media_list.append(InputMediaPhoto(media=file_handle))

                    await update.message.reply_media_group(media=media_list)
                except Exception as e:
                    logger.warning(
                        f"[pic] Error uploading media group: {e}\n{traceback.format_exc()}"
                    )
                    # Don't fail the whole command if media group fails
                finally:
                    # Close all file handles
                    for file_handle in file_handles:
                        try:
                            file_handle.close()
                        except Exception:
                            pass

            await sent_message.delete()

        except Exception as e:
            logger.error(
                f"[pic] Error processing images: {e}\n{traceback.format_exc()}"
            )
            await sent_message.edit_text(
                f"Error processing images: {e!s}"
            )
        finally:
            # Cleanup
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"[pic] Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"[pic] Error cleaning up temp directory: {e}")

    except Exception as e:
        logger.error(
            f"Caught Error in pic.handle - {e} \n {traceback.format_exc()}"
        )
        await update.message.reply_text("Something went wrong while processing your request.")
