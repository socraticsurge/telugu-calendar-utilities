"""LLM-generated Rasi Phalalu for all 12 rashis in a single daily run.

Two-call approach:
  Call 1 — Google Search grounding enabled: the model enriches its
            interpretation with classical Jyotish knowledge.
  Call 2 — response_schema enforced: prose is re-cast into verifiable
            JSON. Every cited transit is checked against the computed
            gochara before the result is accepted.

Retry strategy:
  Each call is retried up to 3 times with exponential backoff on 429.
  If the primary model (gemini-3.1-flash-lite) is exhausted after retries,
  the fallback model (gemma-4-31b) is used without grounding.

Raises VerificationError if the model cites a position or verdict that
does not match the engine output.
"""
import json
import os
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from telugu_panchangam.gochara.rules import gochara_for, named_conditions
from telugu_panchangam.panchangam_names import RASHI_NAMES
from telugu_panchangam.personal.chandrabalam import chandra_position, chandra_verdict

PRIMARY_MODEL = 'gemini-3.1-flash-lite'
FALLBACK_MODEL = 'gemma-4-31b'
TEMPERATURE = 0.65
_MAX_RETRIES = 3
_BASE_DELAY = 2.0  # seconds; doubles each attempt

_SYSTEM_ENRICH = (
    "You are an experienced Jyotish astrologer writing daily Rasi Phalalu for Telugu readers. "
    "Write in clear, flowing English. Tone: warm but grounded, like a knowledgeable elder — "
    "not dramatic or vague. Write a short paragraph (roughly 5–8 sentences) per rasi, giving "
    "each transit its proper weight. Draw on your deep knowledge of classical Jyotish — the "
    "traditional meaning of each graha transiting each house, effects described in the Brihat "
    "Samhita, Sade Sati and Ashtama Shani phases, and the practical impact of vedha. "
    "You MUST base all planetary house positions and verdicts on the data provided; "
    "do not invent or change any graha positions."
)

_SYSTEM_FORMAT = (
    "You are a precise JSON formatter. You will be given: "
    "(1) the computed gochara transit data for a date, and "
    "(2) astrological paragraph text for each of the 12 rashis. "
    "Return a JSON array with one entry per rasi. "
    "For transits_cited, list every graha that was meaningfully discussed in that rasi's "
    "paragraph. Copy position (house number 1–12) and verdict exactly from the input transit "
    "data — do not infer or alter them."
)

_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'rasi': {'type': 'string'},
            'text': {'type': 'string'},
            'transits_cited': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'graha': {'type': 'string'},
                        'position': {'type': 'integer'},
                        'verdict': {'type': 'string'},
                    },
                    'required': ['graha', 'position', 'verdict'],
                },
            },
        },
        'required': ['rasi', 'text', 'transits_cited'],
    },
}


class VerificationError(Exception):
    pass


def _is_rate_limit(e: genai_errors.ClientError) -> bool:
    return '429' in str(e)


def _call_with_retry(fn):
    """Call fn(), retrying up to _MAX_RETRIES times on 429 with exponential backoff."""
    for attempt in range(_MAX_RETRIES):
        try:
            return fn()
        except genai_errors.ClientError as e:
            if _is_rate_limit(e) and attempt < _MAX_RETRIES - 1:
                delay = _BASE_DELAY * (2 ** attempt)
                print(f'429 rate limit, retrying in {delay:.0f}s (attempt {attempt + 1}/{_MAX_RETRIES})')
                time.sleep(delay)
                continue
            raise


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
            if c['verdict'] != cited['verdict']:
                raise VerificationError(
                    f"{rasi}/{graha}: verdict mismatch — "
                    f"computed {c['verdict']!r}, cited {cited['verdict']!r}")


def _enrich(client, model: str, user_prompt: str, use_grounding: bool) -> str:
    config_kwargs = dict(
        system_instruction=_SYSTEM_ENRICH,
        temperature=TEMPERATURE,
    )
    if use_grounding:
        config_kwargs['tools'] = [types.Tool(google_search=types.GoogleSearch())]

    return _call_with_retry(lambda: client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(**config_kwargs),
    ).text)


def _structure(client, model: str, format_prompt: str) -> list[dict]:
    text = _call_with_retry(lambda: client.models.generate_content(
        model=model,
        contents=format_prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_FORMAT,
            response_mime_type='application/json',
            response_schema=_SCHEMA,
            temperature=TEMPERATURE,
        ),
    ).text)
    return json.loads(text)


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
        f"Planetary positions (sidereal, Lahiri ayanamsa):\n{sky_text}\n\n"
        f"Gochara verdicts for all 12 rashis:\n{verdicts_text}\n\n"
        "Write the daily Rasi Phalalu for all 12 rashis."
    )

    format_prompt_template = (
        f"Transit data for {date_str} (use these exact positions and verdicts):\n"
        f"{verdicts_text}\n\n"
        "Astrological paragraphs to format:\n{enriched}"
    )

    client = genai.Client(api_key=os.environ['rasiphalalu'])
    model_used = PRIMARY_MODEL

    try:
        print(f'Call 1: enriching with {PRIMARY_MODEL} (grounding enabled)')
        enriched = _enrich(client, PRIMARY_MODEL, user_prompt, use_grounding=True)
        print(f'Call 2: structuring with {PRIMARY_MODEL}')
        items = _structure(client, PRIMARY_MODEL, format_prompt_template.format(enriched=enriched))
    except genai_errors.ClientError as e:
        if not _is_rate_limit(e):
            raise
        print(f'Primary model exhausted after retries — falling back to {FALLBACK_MODEL}')
        model_used = FALLBACK_MODEL
        enriched = _enrich(client, FALLBACK_MODEL, user_prompt, use_grounding=False)
        items = _structure(client, FALLBACK_MODEL, format_prompt_template.format(enriched=enriched))

    _verify(items, all_rashis)

    return {
        'date': date_str,
        'model_used': model_used,
        'rashis': {item['rasi']: {'text': item['text'],
                                   'transits_cited': item['transits_cited']}
                   for item in items},
    }
