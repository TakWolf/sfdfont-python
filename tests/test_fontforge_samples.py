from pathlib import Path

import pytest

from sfdfont import SfdFont, SfdParseError, SfdUnsupportedError


@pytest.mark.parametrize(
    ('font_file_name', 'error_type', 'message'),
    [
        ('CaslonMM.sfd', SfdUnsupportedError, 'MMCounts:'),
        ('FormalScript.sfd', SfdParseError, 'duplicate glyph ID'),
        ('OmittedCharBugs.sfd', SfdParseError, 'dangling glyph reference'),
        ('SFDBitmapParsing.sfd', SfdParseError, 'BeginChars count'),
        ('SimplifyBugs.sfd', SfdParseError, 'duplicate glyph ID'),
        ('courB18.sfd', SfdParseError, 'duplicate encoding'),
        ('dvng10a-crash.sfd', SfdParseError, 'duplicate glyph ID'),
    ],
)
def test_rejected_fontforge_sample(
    assets_dir: Path,
    font_file_name: str,
    error_type: type[SfdParseError],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        SfdFont.load(assets_dir.joinpath('fontforge', font_file_name))
