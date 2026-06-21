"""LLM-generated Rasi Phalalu for all 12 rashis in a single daily run.

Single-call approach: the model writes rich prose for all 12 rashis and
returns structured JSON in one shot. response_schema enforces the shape;
every cited transit is verified against computed gochara before the
result is accepted.

Uses the Gemini REST API directly (x-goog-api-key header), same pattern
as astro-unified-core. No google-genai SDK dependency.

Retry strategy:
  Each call is retried up to 3 times with exponential backoff on 429.
  If the primary model is exhausted after retries, the fallback model
  is used.

Raises VerificationError if the model cites a position or verdict that
does not match the engine output.
"""
import json
import os
import time

import requests

from telugu_panchangam.gochara.rules import gochara_for, named_conditions
from telugu_panchangam.panchangam_names import RASHI_NAMES
from telugu_panchangam.personal.chandrabalam import chandra_position, chandra_verdict

_API_BASE = 'https://generativelanguage.googleapis.com/v1beta/models'
PRIMARY_MODEL = 'gemini-3.1-flash-lite'
FALLBACK_MODEL = 'gemini-2.0-flash'
TEMPERATURE = 1.0
_MAX_RETRIES = 3
_BASE_DELAY = 10.0

_SYSTEM = (
    "You are a wise Jyotish astrologer writing a daily column for Telugu readers. "
    "Write ONLY in English — do not use Telugu script. "
    "\n\n"
    "For each of the 12 rashis, write ONE flowing paragraph of 10–14 sentences that reads like "
    "a real astrologer's column — practical, warm, personal. Follow this structure:\n"
    "1. Open with the overall tone of the day for this rasi.\n"
    "2. Walk through the key life areas activated today — career, finances, family, health, "
    "relationships — giving each its own 1–2 sentences grounded in the house placements.\n"
    "3. Name the most significant transit causing this energy, described in plain human terms "
    "(e.g. 'Saturn moving through your twelfth house pulls your attention inward').\n"
    "4. If Sade Sati, Ashtama Shani, or vedha applies, mention its practical implication in one sentence.\n"
    "5. Offer at least two concrete things to do or avoid today — specific actions, not vague moods.\n"
    "6. Close with one grounded, encouraging sentence.\n"
    "\n"
    "Tone: warm, direct — address the reader as 'you'. Like advice from a knowledgeable elder. "
    "Never a mere list of verdicts. Each rasi must read distinctly from the others.\n"
    "\n"
    "In addition to the paragraph, write a single 'advice' sentence: the ONE most important "
    "action or mindset for this rasi today. Make it concrete and specific — not 'be patient' "
    "but 'avoid signing contracts or starting negotiations before the afternoon'. "
    "This appears separately as a highlighted callout, so it must stand alone and be self-contained.\n"
    "\n"
    "You MUST ground every house placement and verdict in the data provided. "
    "Do not invent or change any graha positions.\n"
    "\n"
    "Return your response as a JSON array — one object per rasi — with these fields:\n"
    "  'rasi': the rasi name\n"
    "  'text': your paragraph (the full astrologer column text)\n"
    "  'advice': one concrete, self-contained sentence — the single most useful thing to do or avoid today\n"
    "  'transits_cited': array of grahas you discussed, each with 'graha', 'position' (house 1–12), "
    "and 'verdict' (exactly one of: favourable, blocked, adverse — copied from the input data)"
)

_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'rasi': {'type': 'string'},
            'text': {'type': 'string'},
            'advice': {'type': 'string'},
            'transits_cited': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'graha': {'type': 'string'},
                        'position': {'type': 'integer'},
                        'verdict': {'type': 'string', 'enum': ['favourable', 'blocked', 'adverse']},
                    },
                    'required': ['graha', 'position', 'verdict'],
                },
            },
        },
        'required': ['rasi', 'text', 'advice', 'transits_cited'],
    },
}


class VerificationError(Exception):
    pass


def _post(model: str, body: dict) -> str:
    """POST to the Gemini REST API and return the text of the first candidate."""
    api_key = os.environ['rasiphalalu']
    url = f'{_API_BASE}/{model}:generateContent'
    resp = requests.post(
        url,
        headers={
            'Content-Type': 'application/json',
            'x-goog-api-key': api_key,
        },
        json=body,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()['candidates'][0]['content']['parts'][0]['text']


_RETRYABLE = {429, 500, 502, 503, 504}


def _call_with_retry(model: str, body: dict) -> str:
    """Call _post(), retrying up to _MAX_RETRIES times on transient errors."""
    for attempt in range(_MAX_RETRIES):
        try:
            return _post(model, body)
        except requests.HTTPError as e:
            if e.response.status_code in _RETRYABLE and attempt < _MAX_RETRIES - 1:
                delay = _BASE_DELAY * (2 ** attempt)
                print(f'429 rate limit, retrying in {delay:.0f}s (attempt {attempt + 1}/{_MAX_RETRIES})')
                time.sleep(delay)
                continue
            raise


def _generate(model: str, user_prompt: str) -> list[dict]:
    body = {
        'systemInstruction': {'parts': [{'text': _SYSTEM}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        'generationConfig': {
            'temperature': TEMPERATURE,
            'maxOutputTokens': 8192,
            'responseMimeType': 'application/json',
            'responseSchema': _SCHEMA,
        },
    }
    text = _call_with_retry(model, body)
    start = text.find('[')
    end = text.rfind(']')
    if start == -1 or end == -1:
        raise ValueError(f'No JSON array found in model response: {text[:200]!r}')
    return json.loads(text[start:end + 1])


def _compute_all_rashis(sky: dict[str, str]) -> dict:
    result = {}
    for rasi in RASHI_NAMES:
        verdicts = {v['graha']: v for v in gochara_for(rasi, sky)}
        moon_pos = chandra_position(rasi, sky['Chandra'])
        result[rasi] = {
            'verdicts': verdicts,
            'conditions': named_conditions(rasi, sky),
            'moon_house': moon_pos,
            'moon_verdict': chandra_verdict(moon_pos),
        }
    return result


def _format_sky(positions: list[dict]) -> str:
    lines = []
    for p in positions:
        retro = ' (retrograde)' if p.get('retrograde') else ''
        ingress = (f", moves to {p['next_rasi']} on {p['rasi_until']}"
                   if p.get('rasi_until') else '')
        lines.append(
            f"  {p['graha']}: {p['rasi']}, {p['nakshatra']} pada {p['pada']}{retro}{ingress}"
        )
    return '\n'.join(lines)


def _format_verdicts(all_rashis: dict) -> str:
    lines = []
    for rasi, data in all_rashis.items():
        lines.append(f"\n{rasi}:")
        lines.append(f"  Moon: house {data['moon_house']} ({data['moon_verdict']})")
        if data['conditions']:
            lines.append(f"  Special conditions: {', '.join(data['conditions'])}")
        for graha, v in data['verdicts'].items():
            vedha = f" [vedha by {v['vedha_by']}]" if v['vedha_by'] else ''
            lines.append(f"  {graha}: house {v['position']} → {v['verdict']}{vedha}")
    return '\n'.join(lines)


def _verify(items: list[dict], all_rashis: dict) -> None:
    returned_rashis = {item['rasi'] for item in items}
    missing = set(RASHI_NAMES) - returned_rashis
    if missing:
        raise VerificationError(f"Missing rashis in LLM response: {missing}")

    for item in items:
        rasi = item['rasi']
        if rasi not in all_rashis:
            raise VerificationError(f"Unknown rasi in response: {rasi!r}")
        computed = all_rashis[rasi]['verdicts']
        for cited in item['transits_cited']:
            graha = cited['graha']
            if graha not in computed:
                raise VerificationError(
                    f"{rasi}: unknown graha {graha!r} in transits_cited")
            c = computed[graha]
            if c['position'] != cited['position']:
                raise VerificationError(
                    f"{rasi}/{graha}: position mismatch — "
                    f"computed {c['position']}, cited {cited['position']}")
            cited_verdict = cited['verdict'].split()[0].rstrip(',')
            if c['verdict'] != cited_verdict:
                raise VerificationError(
                    f"{rasi}/{graha}: verdict mismatch — "
                    f"computed {c['verdict']!r}, cited {cited['verdict']!r}")


def generate_rasi_phalalu(date_str: str, positions: list[dict]) -> dict:
    """Generate and verify LLM-written Rasi Phalalu for all 12 rashis.

    Parameters
    ----------
    date_str : str
        ISO date string (e.g. '2026-06-19').
    positions : list[dict]
        Output of graha_positions() — nine graha dicts with rasi, nakshatra, etc.

    Returns
    -------
    dict
        {'date': str, 'model_used': str, 'rashis': {rasi: {'text': str, 'transits_cited': [...]}}}

    Raises
    ------
    VerificationError
        If any cited transit position or verdict doesn't match the engine output.
    """
    sky = {p['graha']: p['rasi'] for p in positions}
    all_rashis = _compute_all_rashis(sky)

    sky_text = _format_sky(positions)
    verdicts_text = _format_verdicts(all_rashis)

    user_prompt = (
        f"Today is {date_str}.\n\n"
        f"== Today's sky (sidereal, Lahiri ayanamsa) ==\n{sky_text}\n\n"
        f"== Computed gochara house positions and verdicts for each rasi ==\n"
        f"{verdicts_text}\n\n"
        "Write the daily Rasi Phalalu column for all 12 rashis."
    )

    model_used = PRIMARY_MODEL
    try:
        print(f'Generating with {PRIMARY_MODEL}')
        items = _generate(PRIMARY_MODEL, user_prompt)
    except requests.HTTPError as e:
        if e.response.status_code != 429:
            raise
        print(f'Primary model exhausted after retries — falling back to {FALLBACK_MODEL}')
        model_used = FALLBACK_MODEL
        items = _generate(FALLBACK_MODEL, user_prompt)

    _verify(items, all_rashis)

    return {
        'date': date_str,
        'model_used': model_used,
        'rashis': {item['rasi']: {'text': item['text'],
                                   'advice': item.get('advice', ''),
                                   'transits_cited': item['transits_cited']}
                   for item in items},
    }
