from unittest.mock import MagicMock, patch

import pytest

from fbcm.docx.word_gen import create_rating_ring


@patch("fbcm.docx.word_gen.ImageDraw")
@patch("fbcm.docx.word_gen.ImageFont")
class TestCreateRatingRingFontFallback:
    """Tests for font loading exception handling in create_rating_ring."""

    def test_truetype_success_uses_truetype_font(
        self, mock_image_font, mock_draw, tmp_path
    ):
        mock_font = MagicMock()
        mock_image_font.truetype.return_value = mock_font

        output = str(tmp_path / "ring.png")
        create_rating_ring(75.0, "#FF0000", "#CCCCCC", output_path=output)

        mock_image_font.truetype.assert_called_once()
        mock_image_font.load_default.assert_not_called()

    def test_truetype_os_error_falls_back_to_default(
        self, mock_image_font, mock_draw, tmp_path
    ):
        mock_image_font.truetype.side_effect = OSError("Font not found")
        mock_default = MagicMock()
        mock_image_font.load_default.return_value = mock_default

        output = str(tmp_path / "ring.png")
        create_rating_ring(75.0, "#FF0000", "#CCCCCC", output_path=output)

        mock_image_font.truetype.assert_called_once()
        mock_image_font.load_default.assert_called_once()

    def test_truetype_file_not_found_falls_back_to_default(
        self, mock_image_font, mock_draw, tmp_path
    ):
        mock_image_font.truetype.side_effect = FileNotFoundError("No such file")
        mock_default = MagicMock()
        mock_image_font.load_default.return_value = mock_default

        output = str(tmp_path / "ring.png")
        create_rating_ring(75.0, "#FF0000", "#CCCCCC", output_path=output)

        mock_image_font.load_default.assert_called_once()

    def test_truetype_unexpected_error_propagates(
        self, mock_image_font, mock_draw, tmp_path
    ):
        mock_image_font.truetype.side_effect = ValueError("Unexpected")

        output = str(tmp_path / "ring.png")
        with pytest.raises(ValueError, match="Unexpected"):
            create_rating_ring(75.0, "#FF0000", "#CCCCCC", output_path=output)
