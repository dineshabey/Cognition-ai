"""Backward-compatible re-exports; implementation lives in templates/color_palette.py."""

from templates.color_palette import (  # noqa: F401
    PALETTES,
    PALETTE_CLASSES,
    BerryPalette,
    CitrusPalette,
    ColorPalette,
    EarthPalette,
    ForestPalette,
    MidnightPalette,
    NeonPalette,
    OceanPalette,
    PastelPalette,
    SlatePalette,
    SunsetPalette,
    get_palette,
)

__all__ = [
    "ColorPalette",
    "OceanPalette",
    "SunsetPalette",
    "ForestPalette",
    "MidnightPalette",
    "NeonPalette",
    "PastelPalette",
    "EarthPalette",
    "BerryPalette",
    "SlatePalette",
    "CitrusPalette",
    "PALETTE_CLASSES",
    "PALETTES",
    "get_palette",
]
