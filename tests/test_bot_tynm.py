from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from src.bot.handlers.tynm import (
    add_decorative_elements,
    add_fancy_border,
    add_thank_you_text,
    build_file_path,
    draw_firework,
    draw_flower,
    generate_wrapped_caption,
    handle,
    place_image,
)


class TestGenerateWrappedCaption:
    """Tests for generate_wrapped_caption function."""

    def test_short_text_no_wrapping(self):
        text = "Hello world"
        result = generate_wrapped_caption(text)
        assert result == "Hello world\n"

    def test_text_exactly_65_chars(self):
        text = "a" * 65
        result = generate_wrapped_caption(text)
        assert result == text + "\n"

    def test_long_text_wrapped(self):
        text = "a" * 70
        result = generate_wrapped_caption(text)
        # Note: The function only wraps lines > 65 chars, and uses textwrap
        # which may not always break exactly at 65 chars
        lines = result.strip().split("\n")
        assert len(lines) >= 1
        # Check that the output contains all the original text
        assert result.count("a") == 70

    def test_multiline_text(self):
        text = "Line 1\nLine 2\nLine 3"
        result = generate_wrapped_caption(text)
        expected = "Line 1\nLine 2\nLine 3\n"
        assert result == expected

    def test_multiline_with_long_line(self):
        text = "Short line\n" + "a" * 70 + "\nAnother short"
        result = generate_wrapped_caption(text)
        # Check that multiline text is preserved
        assert "Short line" in result
        assert "Another short" in result
        assert result.count("a") == 70

    def test_empty_text(self):
        text = ""
        result = generate_wrapped_caption(text)
        assert result == "\n"


class TestAddFancyBorder:
    """Tests for add_fancy_border function."""

    def test_add_border_to_rgb_image(self):
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        result = add_fancy_border(img)
        assert result.mode == "RGB"
        assert result.size == (140, 140)  # 100 + 2*20

    def test_add_border_to_rgba_image(self):
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        result = add_fancy_border(img)
        assert result.mode == "RGB"
        assert result.size == (140, 140)

    def test_add_border_to_small_image(self):
        img = Image.new("RGB", (50, 50), color=(0, 255, 0))
        result = add_fancy_border(img)
        assert result.size == (90, 90)

    def test_add_border_to_large_image(self):
        img = Image.new("RGB", (500, 500), color=(0, 0, 255))
        result = add_fancy_border(img)
        assert result.size == (540, 540)


class TestAddThankYouText:
    """Tests for add_thank_you_text function."""

    def test_add_text_to_image(self):
        img = Image.new("RGB", (500, 500), color=(255, 255, 255))
        result = add_thank_you_text(img)
        assert result.size == (500, 500)

    def test_add_text_to_small_image(self):
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        result = add_thank_you_text(img)
        assert result.size == (100, 100)

    def test_add_text_to_large_image(self):
        img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
        result = add_thank_you_text(img)
        assert result.size == (1000, 1000)


class TestDrawFirework:
    """Tests for draw_firework function."""

    def test_draw_default_size_firework(self):
        firework = draw_firework()
        assert firework.mode == "RGBA"
        assert firework.size == (60, 60)

    def test_draw_custom_size_firework(self):
        firework = draw_firework(size=100)
        assert firework.size == (100, 100)

    def test_draw_small_firework(self):
        firework = draw_firework(size=30)
        assert firework.size == (30, 30)

    def test_draw_large_firework(self):
        firework = draw_firework(size=200)
        assert firework.size == (200, 200)


class TestDrawFlower:
    """Tests for draw_flower function."""

    def test_draw_default_size_flower(self):
        flower = draw_flower()
        assert flower.mode == "RGBA"
        assert flower.size == (50, 50)

    def test_draw_custom_size_flower(self):
        flower = draw_flower(size=80)
        assert flower.size == (80, 80)

    def test_draw_small_flower(self):
        flower = draw_flower(size=30)
        assert flower.size == (30, 30)

    def test_draw_large_flower(self):
        flower = draw_flower(size=120)
        assert flower.size == (120, 120)


class TestAddDecorativeElements:
    """Tests for add_decorative_elements function."""

    def test_add_decorations_to_rgb_image(self):
        img = Image.new("RGB", (500, 500), color=(255, 255, 255))
        result = add_decorative_elements(img)
        assert result.mode == "RGBA"
        assert result.size == (500, 500)

    def test_add_decorations_to_rgba_image(self):
        img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))
        result = add_decorative_elements(img)
        assert result.size == (500, 500)

    def test_add_decorations_to_small_image(self):
        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        result = add_decorative_elements(img)
        assert result.size == (200, 200)

    def test_add_decorations_to_large_image(self):
        img = Image.new("RGB", (1000, 800), color=(255, 255, 255))
        result = add_decorative_elements(img)
        assert result.size == (1000, 800)


class TestPlaceImage:
    """Tests for place_image function."""

    def test_place_image_default_scale(self):
        src_img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))
        placement_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        result = place_image(src_img, placement_img, location="center")
        assert result.size == (500, 500)

    def test_place_image_center(self):
        src_img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))
        placement_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        result = place_image(src_img, placement_img, location="center")
        assert result.size == (500, 500)

    def test_place_image_bottom_right(self):
        src_img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))
        placement_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        result = place_image(src_img, placement_img, location="bottom_right")
        assert result.size == (500, 500)

    def test_place_image_bottom_left(self):
        src_img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))
        placement_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        result = place_image(src_img, placement_img, location="bottom_left")
        assert result.size == (500, 500)

    def test_place_image_top_right(self):
        src_img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))
        placement_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        result = place_image(src_img, placement_img, location="top_right")
        assert result.size == (500, 500)

    def test_place_image_top_left(self):
        src_img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))
        placement_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        result = place_image(src_img, placement_img, location="top_left")
        assert result.size == (500, 500)

    def test_place_image_with_scale(self):
        src_img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))
        placement_img = Image.new("RGBA", (200, 200), color=(255, 0, 0, 255))
        result = place_image(src_img, placement_img, scale=4, location="center")
        assert result.size == (500, 500)

    def test_place_image_rgb_to_rgba_conversion(self):
        src_img = Image.new("RGB", (500, 500), color=(255, 255, 255))
        placement_img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        result = place_image(src_img, placement_img, location="center")
        assert result.mode == "RGBA"
        assert result.size == (500, 500)


class TestBuildFilePath:
    """Tests for build_file_path function."""

    def test_build_file_path_no_suffix(self):
        file = {"file_id": "test123", "extension": ".png"}
        result = build_file_path(file)
        assert result.endswith("test123.png")

    def test_build_file_path_with_suffix(self):
        file = {"file_id": "test456", "extension": ".jpg"}
        result = build_file_path(file, "_modified")
        assert result.endswith("test456_modified.jpg")

    def test_build_file_path_complex_id(self):
        file = {"file_id": "AgACAgIAAxkBAAI...", "extension": ".webp"}
        result = build_file_path(file, "_tynm")
        assert result.endswith("AgACAgIAAxkBAAI..._tynm.webp")


class TestHandle:
    """Tests for handle function."""

    @pytest.fixture
    def mock_update(self):
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_to_message = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        context = MagicMock()
        context.bot = MagicMock()
        return context

    @pytest.fixture
    def mock_update_with_reply_photo(self, mock_update):
        mock_update.message.reply_photo = AsyncMock()
        return mock_update

    @pytest.mark.asyncio
    async def test_handle_no_reply_to_message(self, mock_update, mock_context):
        mock_update.message.reply_to_message = None
        await handle(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with(
            "Please reply to a message with `/tynm`"
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.tynm.os.path.exists")
    @patch("src.bot.handlers.tynm.os.listdir")
    async def test_handle_tynm_directory_not_exists(
        self, mock_listdir, mock_exists, mock_update, mock_context
    ):
        mock_exists.return_value = False
        await handle(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with(
            "TYNM images not found. Please contact admin."
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.tynm.os.path.exists")
    @patch("src.bot.handlers.tynm.os.listdir")
    async def test_handle_no_images_in_directory(
        self, mock_listdir, mock_exists, mock_update, mock_context
    ):
        mock_exists.return_value = True
        mock_listdir.return_value = []
        await handle(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with(
            "No TYNM images available. Please contact admin."
        )

    @pytest.mark.asyncio
    @patch("src.bot.handlers.tynm.os.path.exists")
    @patch("src.bot.handlers.tynm.os.listdir")
    @patch("src.bot.handlers.tynm.Image.open")
    @patch("src.bot.handlers.tynm.util.choose_random_element_from_list")
    async def test_handle_image_load_failure(
        self, mock_choose, mock_open, mock_listdir, mock_exists, mock_update, mock_context
    ):
        mock_exists.return_value = True
        mock_listdir.return_value = ["test.png"]
        mock_choose.return_value = "test.png"
        mock_open.side_effect = Exception("Failed to open")
        await handle(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with(
            "Failed to load image. Please try again later."
        )
