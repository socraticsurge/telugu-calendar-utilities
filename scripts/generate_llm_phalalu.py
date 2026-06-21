"""Daily script: generate LLM-written Rasi Phalalu for all 12 rashis.

Positions are taken at Hyderabad sunrise (rasi-level data is uniform
across Indian cities at this resolution).

Usage:
    GEMINI_API_KEY=<key> python scripts/generate_llm_phalalu.py

Output:
    data/llm_phalalu/YYYY-MM-DD.json   (override with PHALALU_OUT env var)

Exits non-zero on verification failure so CI/cron alerts loudly.
"""
import json
import os
import sys
from datetime import date

from telugu_panchangam.engines.utils import get_sunrise, local_midnight_jd
from telugu_panchangam.gochara.positions import graha_positions
from telugu_panchangam.personal.llm_phalalu import VerificationError, generate_rasi_phalalu

HYD_GEO = [78.4744, 17.3850, 0.0]

if __name__ == '__main__':
    if not os.environ.get('rasiphalalu'):
        print('Error: rasiphalalu environment variable not set.', file=sys.stderr)
        sys.exit(1)

    today = date.today()
    jd = get_sunrise(local_midnight_jd(today, 'Asia/Kolkata'), HYD_GEO)
    positions = graha_positions(jd)

    try:
        result = generate_rasi_phalalu(today.isoformat(), positions)
    except VerificationError as e:
        print(f'Verification failed: {e}', file=sys.stderr)
        sys.exit(1)

    out_dir = os.environ.get('PHALALU_OUT', 'data/llm_phalalu')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{today.isoformat()}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f'Wrote {out_path}')
