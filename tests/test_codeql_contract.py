"""Static contracts that keep previously cleared CodeQL noise from returning."""

import io
import token
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_activity_rules_uses_explicit_multiline_string_concatenation():
    source = (ROOT / 'telugu_panchangam/personal/activity_rules.py').read_text()
    ignored = {
        tokenize.COMMENT,
        tokenize.DEDENT,
        tokenize.INDENT,
        tokenize.NL,
    }
    significant = [
        item
        for item in tokenize.generate_tokens(io.StringIO(source).readline)
        if item.type not in ignored
    ]
    implicit_lines = [
        current.start[0]
        for previous, current in zip(significant, significant[1:])
        if previous.type == token.STRING and current.type == token.STRING
    ]

    assert implicit_lines == [], (
        'Use an explicit + between multiline string fragments; implicit '
        f'concatenation starts on lines {implicit_lines}'
    )
