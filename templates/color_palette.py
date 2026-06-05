"""Six-color hex palettes for word clouds and UI theming."""

from __future__ import annotations

import random
import re
from typing import ClassVar, Iterator, Sequence

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_PALETTE_SIZE = 6


def _validate_hex(color: str) -> str:
    if not _HEX_RE.match(color):
        raise ValueError(
            "Invalid hex color {!r}; expected format #RRGGBB.".format(color)
        )
    return color.lower()


class ColorPalette:
    """A fixed set of six hex colors (#RRGGBB)."""

    name: ClassVar[str] = "custom"
    _colors: tuple[str, ...]

    def __init__(self, colors: Sequence[str], *, name: str | None = None):
        if len(colors) != _PALETTE_SIZE:
            raise ValueError(
                "Palette must contain exactly {} colors, got {}.".format(
                    _PALETTE_SIZE, len(colors)
                )
            )
        self._colors = tuple(_validate_hex(c) for c in colors)
        if name is not None:
            self.name = name

    @property
    def colors(self) -> tuple[str, ...]:
        return self._colors

    def as_list(self) -> list[str]:
        return list(self._colors)

    def random_color(self) -> str:
        return random.choice(self._colors)

    def __iter__(self) -> Iterator[str]:
        return iter(self._colors)

    def __len__(self) -> int:
        return _PALETTE_SIZE

    def __getitem__(self, index: int) -> str:
        return self._colors[index]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ColorPalette):
            return NotImplemented
        return self.name == other.name and self._colors == other._colors

    def __repr__(self) -> str:
        return "ColorPalette(name={!r}, colors={})".format(self.name, self._colors)


class OceanPalette(ColorPalette):
    """Cool blues and teals."""

    name = "ocean"

    def __init__(self) -> None:
        super().__init__(
            (
                "#0077b6",
                "#00b4d8",
                "#90e0ef",
                "#48cae4",
                "#023e8a",
                "#0096c7",
            ),
            name=self.name,
        )


class SunsetPalette(ColorPalette):
    """Warm oranges, corals, and magentas."""

    name = "sunset"

    def __init__(self) -> None:
        super().__init__(
            (
                "#ff6b6b",
                "#ee5a24",
                "#f368e0",
                "#ff9f43",
                "#ff7979",
                "#eb4d4b",
            ),
            name=self.name,
        )


class ForestPalette(ColorPalette):
    """Natural greens."""

    name = "forest"

    def __init__(self) -> None:
        super().__init__(
            (
                "#2d6a4f",
                "#40916c",
                "#52b788",
                "#74c69d",
                "#1b4332",
                "#95d5b2",
            ),
            name=self.name,
        )


class MidnightPalette(ColorPalette):
    """Dark-theme accents (matches the web app word cloud)."""

    name = "midnight"

    def __init__(self) -> None:
        super().__init__(
            (
                "#60a5fa",
                "#34d399",
                "#a78bfa",
                "#f472b6",
                "#fbbf24",
                "#38bdf8",
            ),
            name=self.name,
        )


class NeonPalette(ColorPalette):
    """High-contrast neon hues."""

    name = "neon"

    def __init__(self) -> None:
        super().__init__(
            (
                "#39ff14",
                "#ff073a",
                "#00ffff",
                "#ff10f0",
                "#ffff00",
                "#bf00ff",
            ),
            name=self.name,
        )


class PastelPalette(ColorPalette):
    """Soft pastel tones."""

    name = "pastel"

    def __init__(self) -> None:
        super().__init__(
            (
                "#ffc8dd",
                "#ffafcc",
                "#bde0fe",
                "#a2d2ff",
                "#cdb4db",
                "#e2ece9",
            ),
            name=self.name,
        )


class EarthPalette(ColorPalette):
    """Browns, sand, and clay."""

    name = "earth"

    def __init__(self) -> None:
        super().__init__(
            (
                "#6f4e37",
                "#a47148",
                "#c9a66b",
                "#8b5e3c",
                "#d4a373",
                "#e9c46a",
            ),
            name=self.name,
        )


class BerryPalette(ColorPalette):
    """Purples and reds."""

    name = "berry"

    def __init__(self) -> None:
        super().__init__(
            (
                "#5a189a",
                "#7b2cbf",
                "#9d4edd",
                "#c77dff",
                "#e0aaff",
                "#ff006e",
            ),
            name=self.name,
        )


class SlatePalette(ColorPalette):
    """Neutral grays and blue-grays."""

    name = "slate"

    def __init__(self) -> None:
        super().__init__(
            (
                "#334155",
                "#475569",
                "#64748b",
                "#94a3b8",
                "#cbd5e1",
                "#1e293b",
            ),
            name=self.name,
        )


class CitrusPalette(ColorPalette):
    """Yellows, limes, and oranges."""

    name = "citrus"

    def __init__(self) -> None:
        super().__init__(
            (
                "#f9c74f",
                "#f9844a",
                "#f8961e",
                "#90be6d",
                "#43aa8b",
                "#577590",
            ),
            name=self.name,
        )


PALETTE_CLASSES: tuple[type[ColorPalette], ...] = (
    OceanPalette,
    SunsetPalette,
    ForestPalette,
    MidnightPalette,
    NeonPalette,
    PastelPalette,
    EarthPalette,
    BerryPalette,
    SlatePalette,
    CitrusPalette,
)

PALETTES: dict[str, ColorPalette] = {
    cls.name: cls() for cls in PALETTE_CLASSES
}


def get_palette(name: str) -> ColorPalette:
    """Return a built-in palette by name (case-insensitive)."""
    key = name.strip().lower()
    try:
        return PALETTES[key]
    except KeyError:
        available = ", ".join(sorted(PALETTES))
        raise KeyError(
            "Unknown palette {!r}. Available: {}.".format(name, available)
        ) from None


def get_all_palettes() -> list[dict[str, object]]:
    """Return all built-in palettes for the UI (stable display order)."""
    return [
        {
            "name": cls.name,
            "label": cls.name.replace("_", " ").title(),
            "colors": PALETTES[cls.name].as_list(),
        }
        for cls in PALETTE_CLASSES
    ]

