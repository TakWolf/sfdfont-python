from pathlib import Path

import pytest

from sfdfont import SfdFont


@pytest.mark.parametrize(
    ('font_dir', 'font_file_name'),
    [
        ('fontforge', 'AHBugs.sfd'),
        ('fontforge', 'AddExtremaTest2.sfd'),
        ('fontforge', 'AddExtremumTest.sfd'),
        ('fontforge', 'Ambrosia.sfd'),
        ('fontforge', 'AmbrosiaBold.sfd'),
        ('fontforge', 'AmbrosiaItalic.sfd'),
        ('fontforge', 'BoxesAndBounds.sfd'),
        ('fontforge', 'CMAPEncTest.sfd'),
        ('fontforge', 'Caliban.sfd'),
        ('fontforge', 'DejaVuSerif.sfd'),
        ('fontforge', 'DirectionTest.sfd'),
        ('fontforge', 'Hinting.sfd'),
        ('fontforge', 'ItalicHand.sfd'),
        ('fontforge', 'NimbusLGCUni-Regular.sfd'),
        ('fontforge', 'NumberPoints.sfd'),
        ('fontforge', 'OverlapBugs.sfd'),
        ('fontforge', 'QuadOverlapBugs.sfd'),
        ('fontforge', 'QuadraticConversionBug.sfd'),
        ('fontforge', 'SplineOverlapBug1.sfd'),
        ('fontforge', 'StrokeTests.sfd'),
        ('fontforge', 'VKern.sfd'),
    ],
)
def test_load_save(
    assets_dir: Path,
    font_dir: str,
    font_file_name: str,
    tmp_path: Path,
) -> None:
    load_path = assets_dir.joinpath(font_dir, font_file_name)
    save_path = tmp_path.joinpath(font_file_name)
    font = SfdFont.load(load_path)
    font.save(save_path)
    saved_data = save_path.read_bytes()
    saved_font = SfdFont.load(save_path)
    assert saved_font == font
    saved_font.save(save_path)
    assert save_path.read_bytes() == saved_data
