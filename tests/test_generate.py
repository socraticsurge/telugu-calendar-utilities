# tests/test_generate.py
import os
import tempfile
from datetime import date
from telugu_panchangam.generate import generate_feeds

def test_generate_creates_ics_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        start = date(2024, 3, 24)
        end = date(2024, 3, 26)
        generate_feeds(output_dir=tmpdir, start=start, end=end,
                       systems=['drik'], city_names=['Hyderabad'])
        files = os.listdir(tmpdir)
        assert 'hyderabad-drik.ics' in files

def test_generate_file_is_nonempty():
    with tempfile.TemporaryDirectory() as tmpdir:
        start = date(2024, 3, 24)
        end = date(2024, 3, 26)
        generate_feeds(output_dir=tmpdir, start=start, end=end,
                       systems=['drik'], city_names=['Hyderabad'])
        path = os.path.join(tmpdir, 'hyderabad-drik.ics')
        assert os.path.getsize(path) > 100
