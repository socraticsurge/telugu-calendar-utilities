"""Protect research transcription integrity, not engine correctness."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs/research/vakya-1962-lunar-table'


def test_numeric_transcription_is_complete_and_csv_matches_json():
    rows = json.loads((ROOT / 'lunar-longitudes.json').read_text())
    with (ROOT / 'lunar-longitudes.csv').open() as source:
        csv_rows = list(csv.DictReader(source))
    assert [row['day'] for row in rows] == list(range(1, 249))
    assert len(csv_rows) == len(rows)
    for row, csv_row in zip(rows, csv_rows):
        for field in ('day', 'physical_pdf_page', 'printed_page', 'row_on_page',
                      'rasi', 'degree', 'arcminute'):
            assert int(csv_row[field]) == row[field]
        assert 0 <= row['rasi'] < 12
        assert 0 <= row['degree'] < 30
        assert 0 <= row['arcminute'] < 60
        assert row['pdf_page_index'] == row['physical_pdf_page'] - 1


def test_printed_complement_discrepancy_remains_explicit_and_uncorrected():
    rows = json.loads((ROOT / 'lunar-longitudes.json').read_text())
    minutes = {row['day']: row['rasi'] * 1800 + row['degree'] * 60
               + row['arcminute'] for row in rows}
    target = minutes[248]
    mismatches = [(day, 248 - day,
                   (minutes[day] + minutes[248 - day]) % 21600 - target)
                  for day in range(1, 125)
                  if (minutes[day] + minutes[248 - day]) % 21600 != target]
    assert mismatches == [(100, 148, -10)]
    assert rows[99]['arcminute'] == rows[147]['arcminute'] == 17
    assert target == 27 * 60 + 44
