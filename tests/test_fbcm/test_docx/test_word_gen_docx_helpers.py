"""Tests for DOCX helper functions and WordDocGenerator methods in fbcm.docx.word_gen."""

import json

import pytest
from docx import Document
from docx.oxml.ns import qn

from fbcm.docx.word_gen import (
    WordDocGenerator,
    add_left_border,
    remove_cell_borders,
    set_cell_margins,
    set_cell_shading,
)
from fbcm.models import (
    BasicInfo,
    DefenseStats,
    InterceptionStats,
    OffenseSkillPlayerStats,
    PassingStats,
    ProspectDataSoup,
    ReceivingStats,
    RushingStats,
    TackleStats,
)


@pytest.fixture
def doc_cell():
    """Create a real DOCX cell for testing XML manipulation helpers."""
    doc = Document()
    table = doc.add_table(rows=1, cols=1)
    return table.cell(0, 0)


class TestSetCellShading:
    def test_sets_fill_color(self, doc_cell):
        set_cell_shading(doc_cell, "#FF0000")
        tcPr = doc_cell._tc.get_or_add_tcPr()
        shd = tcPr.find(qn("w:shd"))
        assert shd is not None
        assert shd.get(qn("w:fill")) == "FF0000"

    def test_strips_hash_prefix(self, doc_cell):
        set_cell_shading(doc_cell, "00FF00")
        tcPr = doc_cell._tc.get_or_add_tcPr()
        shd = tcPr.find(qn("w:shd"))
        assert shd.get(qn("w:fill")) == "00FF00"

    def test_replaces_existing_shading(self, doc_cell):
        set_cell_shading(doc_cell, "#FF0000")
        set_cell_shading(doc_cell, "#00FF00")
        tcPr = doc_cell._tc.get_or_add_tcPr()
        shd_elements = tcPr.findall(qn("w:shd"))
        assert len(shd_elements) == 1
        assert shd_elements[0].get(qn("w:fill")) == "00FF00"

    def test_sets_val_and_color_attributes(self, doc_cell):
        set_cell_shading(doc_cell, "#AABBCC")
        tcPr = doc_cell._tc.get_or_add_tcPr()
        shd = tcPr.find(qn("w:shd"))
        assert shd.get(qn("w:val")) == "clear"
        assert shd.get(qn("w:color")) == "auto"


class TestSetCellMargins:
    def test_sets_all_margins(self, doc_cell):
        set_cell_margins(doc_cell, top=100, bottom=80, left=60, right=40)
        tcPr = doc_cell._tc.get_or_add_tcPr()
        tcMar = tcPr.find(qn("w:tcMar"))
        assert tcMar is not None

        top = tcMar.find(qn("w:top"))
        assert top.get(qn("w:w")) == "100"
        assert top.get(qn("w:type")) == "dxa"

        bottom = tcMar.find(qn("w:bottom"))
        assert bottom.get(qn("w:w")) == "80"

        left = tcMar.find(qn("w:left"))
        assert left.get(qn("w:w")) == "60"

        right = tcMar.find(qn("w:right"))
        assert right.get(qn("w:w")) == "40"

    def test_replaces_existing_margins(self, doc_cell):
        set_cell_margins(doc_cell, top=100)
        set_cell_margins(doc_cell, top=200)
        tcPr = doc_cell._tc.get_or_add_tcPr()
        tcMar_elements = tcPr.findall(qn("w:tcMar"))
        assert len(tcMar_elements) == 1
        top = tcMar_elements[0].find(qn("w:top"))
        assert top.get(qn("w:w")) == "200"

    def test_default_margins_are_zero(self, doc_cell):
        set_cell_margins(doc_cell)
        tcPr = doc_cell._tc.get_or_add_tcPr()
        tcMar = tcPr.find(qn("w:tcMar"))
        for margin_name in ["top", "bottom", "left", "right"]:
            margin = tcMar.find(qn(f"w:{margin_name}"))
            assert margin.get(qn("w:w")) == "0"


class TestRemoveCellBorders:
    def test_sets_nil_borders(self, doc_cell):
        remove_cell_borders(doc_cell)
        tcPr = doc_cell._tc.get_or_add_tcPr()
        tcBorders = tcPr.find(qn("w:tcBorders"))
        assert tcBorders is not None

        for border_name in ["top", "left", "bottom", "right"]:
            border = tcBorders.find(qn(f"w:{border_name}"))
            assert border is not None
            assert border.get(qn("w:val")) == "nil"

    def test_replaces_existing_borders(self, doc_cell):
        remove_cell_borders(doc_cell)
        remove_cell_borders(doc_cell)
        tcPr = doc_cell._tc.get_or_add_tcPr()
        tcBorders_elements = tcPr.findall(qn("w:tcBorders"))
        assert len(tcBorders_elements) == 1


class TestAddLeftBorder:
    def test_adds_left_border(self, doc_cell):
        add_left_border(doc_cell, "#FF0000", size=24)
        tcPr = doc_cell._tc.get_or_add_tcPr()
        tcBorders = tcPr.find(qn("w:tcBorders"))

        left = tcBorders.find(qn("w:left"))
        assert left is not None
        assert left.get(qn("w:val")) == "single"
        assert left.get(qn("w:sz")) == "24"
        assert left.get(qn("w:color")) == "FF0000"

    def test_other_borders_are_nil(self, doc_cell):
        add_left_border(doc_cell, "#FF0000")
        tcPr = doc_cell._tc.get_or_add_tcPr()
        tcBorders = tcPr.find(qn("w:tcBorders"))

        for border_name in ["top", "bottom", "right"]:
            border = tcBorders.find(qn(f"w:{border_name}"))
            assert border.get(qn("w:val")) == "nil"

    def test_strips_hash_from_color(self, doc_cell):
        add_left_border(doc_cell, "AABB00")
        tcPr = doc_cell._tc.get_or_add_tcPr()
        left = tcPr.find(qn("w:tcBorders")).find(qn("w:left"))
        assert left.get(qn("w:color")) == "AABB00"


def _make_colors_file(tmp_path):
    """Create a test school colors JSON file."""
    colors_data = {
        "FBS": {
            "ACC": {
                "Miami": {
                    "primary": "#F47321",
                    "secondary": "#005030",
                    "light": "#FDE8D3",
                }
            }
        }
    }
    colors_file = tmp_path / "colors.json"
    colors_file.write_text(json.dumps(colors_data))
    return str(colors_file)


class TestWordDocGeneratorGetStatValue:
    @pytest.fixture
    def generator(self, tmp_path):
        colors_file = _make_colors_file(tmp_path)
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path / "rings"),
            colors_path=colors_file,
        )
        return gen

    def test_returns_dash_when_no_stats(self, generator):
        generator.prospect = ProspectDataSoup(
            basic_info=BasicInfo(position="QB"), stats=None
        )
        assert generator._get_stat_value("Passing", "CMP") == "\u2014"

    def test_flat_stats_passing(self, generator):
        generator.prospect = ProspectDataSoup(
            basic_info=BasicInfo(position="QB"),
            stats=PassingStats(cmp=280, att=420, yds=3800, td=32),
        )
        assert generator._get_stat_value("Passing", "CMP") == "280"
        assert generator._get_stat_value("Passing", "ATT") == "420"
        assert generator._get_stat_value("Passing", "TD") == "32"

    def test_nested_stats_rushing(self, generator):
        generator.prospect = ProspectDataSoup(
            basic_info=BasicInfo(position="RB"),
            stats=OffenseSkillPlayerStats(
                rushing=RushingStats(att=200, yds=1200, td=14),
                receiving=ReceivingStats(rec=30, yds=250),
            ),
        )
        assert generator._get_stat_value("Rushing", "ATT") == "200"
        assert generator._get_stat_value("Rushing", "YDS") == "1200"
        assert generator._get_stat_value("Receiving", "REC") == "30"

    def test_nested_stats_defense(self, generator):
        generator.prospect = ProspectDataSoup(
            basic_info=BasicInfo(position="DL"),
            stats=DefenseStats(
                tackle=TackleStats(total=65, solo=42, sacks=8.5),
                interception=InterceptionStats(ints=2, pds=10),
            ),
        )
        assert generator._get_stat_value("Tackles", "TOTAL") == "65"
        assert generator._get_stat_value("Interceptions", "INTS") == "2"

    def test_returns_dash_for_missing_nested_category(self, generator):
        generator.prospect = ProspectDataSoup(
            basic_info=BasicInfo(position="RB"),
            stats=OffenseSkillPlayerStats(rushing=None, receiving=None),
        )
        assert generator._get_stat_value("Rushing", "ATT") == "\u2014"

    def test_int_maps_to_ints(self, generator):
        generator.prospect = ProspectDataSoup(
            basic_info=BasicInfo(position="QB"),
            stats=PassingStats(ints=8),
        )
        assert generator._get_stat_value("Passing", "INT") == "8"

    def test_rtg_maps_to_qb_rtg(self, generator):
        generator.prospect = ProspectDataSoup(
            basic_info=BasicInfo(position="QB"),
            stats=PassingStats(qb_rtg=155.2),
        )
        assert generator._get_stat_value("Passing", "RTG") == "155.2"

    def test_tds_maps_to_td(self, generator):
        generator.prospect = ProspectDataSoup(
            basic_info=BasicInfo(position="DL"),
            stats=DefenseStats(
                interception=InterceptionStats(td=3),
            ),
        )
        assert generator._get_stat_value("Interceptions", "TDS") == "3"


class TestWordDocGeneratorCleanupRingImages:
    def test_removes_existing_ring_images(self, tmp_path):
        colors_file = _make_colors_file(tmp_path)
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path / "rings"),
            colors_path=colors_file,
        )

        ring1 = tmp_path / "ring1.png"
        ring2 = tmp_path / "ring2.png"
        ring1.write_bytes(b"fake")
        ring2.write_bytes(b"fake")

        gen._ring_img_paths = [str(ring1), str(ring2)]
        gen._cleanup_ring_images()

        assert not ring1.exists()
        assert not ring2.exists()
        assert len(gen._ring_img_paths) == 0

    def test_handles_already_deleted_files(self, tmp_path):
        colors_file = _make_colors_file(tmp_path)
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path / "rings"),
            colors_path=colors_file,
        )

        gen._ring_img_paths = [str(tmp_path / "nonexistent.png")]
        gen._cleanup_ring_images()  # Should not raise
        assert len(gen._ring_img_paths) == 0


class TestWordDocGeneratorGenerateCompleteDocument:
    @pytest.fixture
    def generator(self, tmp_path):
        colors_file = _make_colors_file(tmp_path)
        gen = WordDocGenerator(
            output_path=str(tmp_path),
            ring_image_base_dir=str(tmp_path / "rings"),
            colors_path=colors_file,
        )
        return gen

    def test_uses_explicit_filename(self, generator, tmp_path):
        generator.generate_complete_document(filename="custom.docx")
        assert (tmp_path / "custom.docx").exists()

    def test_single_prospect_uses_name(self, generator, tmp_path):
        generator._prospect_count = 1
        generator._last_prospect_name = "Cam Ward"
        generator.generate_complete_document()
        assert (tmp_path / "Cam Ward.docx").exists()

    def test_multiple_prospects_uses_default_name(self, generator, tmp_path):
        generator._prospect_count = 3
        generator.generate_complete_document()
        assert (tmp_path / "prospects.docx").exists()

    def test_cleans_up_ring_images_after_save(self, generator, tmp_path):
        ring_file = tmp_path / "test_ring.png"
        ring_file.write_bytes(b"fake")
        generator._ring_img_paths = [str(ring_file)]

        generator.generate_complete_document(filename="output.docx")
        assert not ring_file.exists()
