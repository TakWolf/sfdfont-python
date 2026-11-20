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
        ('fontforge', 'NumberPoints.sfd'),
        ('fontforge', 'OverlapBugs.sfd'),
        ('fontforge', 'QuadOverlapBugs.sfd'),
        ('fontforge', 'QuadraticConversionBug.sfd'),
        ('fontforge', 'SplineOverlapBug1.sfd'),
        ('fontforge', 'StrokeTests.sfd'),
    ],
)
def test_parse_dump(
    assets_dir: Path,
    font_dir: str,
    font_file_name: str,
) -> None:
    data = assets_dir.joinpath(font_dir, font_file_name).read_bytes()
    font = SfdFont.parse(data)
    dumped_data = font.dump_to_bytes()
    dumped_font = SfdFont.parse(dumped_data)
    assert dumped_font == font
    assert dumped_font.dump_to_bytes() == dumped_data
