from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image, ImageDraw, ImageFont

from src.bot.handlers.tynm import (
    FONT_POOL_GREETING,
    POSTER_HEIGHT,
    POSTER_LAYOUTS,
    POSTER_SIZE,
    POSTER_WIDTH,
    add_decorative_elements,
    add_fancy_border,
    add_poster_bottom_banner,
    add_poster_decorations,
    add_thank_you_text,
    apply_modi_layout,
    build_file_path,
    choose_poster_layout,
    create_saffron_gradient,
    draw_centered_multiline_in_box,
    draw_firework,
    draw_flower,
    extract_reply_text,
    generate_wrapped_caption,
    get_poster_caption_font_size,
    handle,
    load_font_from_pool,
    make_circular_portrait,
    measure_text,
    pick_distinct_tynm_images,
    place_image,
)


class TestExtractReplyText:
    """Tests for extract_reply_text function."""

    def test_extracts_text(self):
        reply = MagicMock()
        reply.text = "https://github.com/arkits/chaddi-tg"
        reply.caption = None
        assert extract_reply_text(reply) == "https://github.com/arkits/chaddi-tg"

    def test_extracts_caption_when_no_text(self):
        reply = MagicMock()
        reply.text = None
        reply.caption = "caption text"
        assert extract_reply_text(reply) == "caption text"

    def test_prefers_text_over_caption(self):
        reply = MagicMock()
        reply.text = "message text"
        reply.caption = "caption text"
        assert extract_reply_text(reply) == "message text"

    def test_returns_none_when_empty(self):
        reply = MagicMock()
        reply.text = None
        reply.caption = None
        assert extract_reply_text(reply) is None


class TestMeasureText:
    """Tests for measure_text function."""

    def test_measure_text_returns_dimensions(self):
        img = Image.new("RGBA", (100, 100))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        width, height = measure_text(draw, "hello", font)
        assert width > 0
        assert height > 0


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


class TestPosterHelpers:
    """Tests for poster-style tynm helpers."""

    def test_poster_is_square(self):
        assert POSTER_WIDTH == POSTER_HEIGHT == POSTER_SIZE == 1280

    def test_create_saffron_gradient_size(self):
        result = create_saffron_gradient(POSTER_WIDTH, POSTER_HEIGHT)
        assert result.mode == "RGBA"
        assert result.size == (POSTER_WIDTH, POSTER_HEIGHT)

    def test_choose_poster_layout(self):
        layout = choose_poster_layout()
        assert layout in POSTER_LAYOUTS

    def test_apply_modi_layout(self):
        img = create_saffron_gradient(POSTER_WIDTH, POSTER_HEIGHT)
        foreground_modi = Image.new("RGBA", (200, 400), color=(255, 0, 0, 255))
        watermark_modi = Image.new("RGBA", (180, 360), color=(0, 255, 0, 255))
        layout = POSTER_LAYOUTS[0]
        result = apply_modi_layout(img, foreground_modi, watermark_modi, layout)
        assert result.size == (POSTER_WIDTH, POSTER_HEIGHT)

    def test_pick_distinct_tynm_images(self):
        files = ["a.png", "b.png", "c.png"]
        result = pick_distinct_tynm_images(files, 2)
        assert len(result) == 2
        assert result[0] != result[1]

    def test_pick_distinct_tynm_images_single_file_fallback(self):
        result = pick_distinct_tynm_images(["only.png"], 2)
        assert result == ["only.png", "only.png"]

    def test_load_font_from_pool(self):
        font = load_font_from_pool(FONT_POOL_GREETING, 32)
        assert font is not None

    def test_draw_centered_multiline_in_box(self):
        img = create_saffron_gradient(POSTER_WIDTH, POSTER_HEIGHT)
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw_centered_multiline_in_box(
            draw,
            (100, 100, 500, 300),
            "centered\nmessage",
            font,
            (255, 255, 255),
        )
        assert img.size == (POSTER_WIDTH, POSTER_HEIGHT)

    def test_get_poster_caption_font_size(self):
        assert get_poster_caption_font_size(2) == 58
        assert get_poster_caption_font_size(5) == 44
        assert get_poster_caption_font_size(11) == 28

    def test_make_circular_portrait(self):
        profile = Image.new("RGB", (300, 400), color=(100, 150, 200))
        result = make_circular_portrait(profile, 120)
        assert result.mode == "RGBA"
        assert result.size[0] == result.size[1]

    def test_add_poster_bottom_banner(self):
        img = create_saffron_gradient(POSTER_WIDTH, POSTER_HEIGHT)
        result = add_poster_bottom_banner(img, "~ testuser", "01/01/2026, 08:00 AM", "Test Group")
        assert result.size == (POSTER_WIDTH, POSTER_HEIGHT)

    def test_add_poster_decorations(self):
        img = create_saffron_gradient(POSTER_WIDTH, POSTER_HEIGHT)
        result = add_poster_decorations(img)
        assert result.mode == "RGBA"
        assert result.size == (POSTER_WIDTH, POSTER_HEIGHT)


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
    async def test_handle_unsupported_reply_type(
        self, mock_choose, mock_open, mock_listdir, mock_exists, mock_update, mock_context
    ):
        mock_exists.return_value = True
        mock_listdir.return_value = ["test.png"]
        mock_choose.return_value = "test.png"
        mock_open.return_value = Image.new("RGBA", (100, 100), color=(255, 255, 255, 255))

        reply_message = mock_update.message.reply_to_message
        reply_message.text = None
        reply_message.caption = None
        reply_message.photo = None

        await handle(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with(
            "Please reply to a photo or text message with `/tynm`"
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
