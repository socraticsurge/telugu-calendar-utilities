"""Shared day/night Choghadiya sequencing.

The day engine owns sunrise-to-sunset Choghadiya. Night blocks use the
traditional weekday sequence from sunset to the following sunrise. Keeping the
night table here prevents the feed generator, Muhurtam scorer and HTTP/MCP
serializers from drifting apart.
"""

from telugu_panchangam.models.panchangam_day import PanchangamDay, Window


# Weekday 0=Sunday, matching the Panchangam engines.
NIGHT_CHOGHADIYA_NAMES = {
    0: ["Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh"],
    1: ["Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char"],
    2: ["Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal"],
    3: ["Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg"],
    4: ["Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit"],
    5: ["Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog"],
    6: ["Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh"],
}


def night_choghadiya(day: PanchangamDay, next_day: PanchangamDay) -> list[Window]:
    """Return the eight blocks from today's sunset to tomorrow's sunrise."""
    weekday = (day.date.weekday() + 1) % 7
    block_duration = (next_day.sunrise - day.sunset) / 8
    return [
        Window(
            name=NIGHT_CHOGHADIYA_NAMES[weekday][index],
            start=day.sunset + index * block_duration,
            end=day.sunset + (index + 1) * block_duration,
        )
        for index in range(8)
    ]
