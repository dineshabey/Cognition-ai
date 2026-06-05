"""Tests for ColorPalette and built-in palettes."""

import pytest

from templates.color_palette import (
    PALETTES,
    PALETTE_CLASSES,
    BerryPalette,
    ColorPalette,
    MidnightPalette,
    OceanPalette,
    SunsetPalette,
    get_all_palettes,
    get_palette,
)


def test_palette_requires_six_colors():
    with pytest.raises(ValueError, match="exactly 6"):
        ColorPalette(["#000000"] * 5)
    with pytest.raises(ValueError, match="exactly 6"):
        ColorPalette(["#000000"] * 7)


def test_invalid_hex_raises():
    with pytest.raises(ValueError, match="Invalid hex"):
        ColorPalette(["#gggggg"] * 6)


def test_custom_palette_normalizes_hex():
    p = ColorPalette(["#AABBCC", "#112233", "#445566", "#778899", "#AABBCC", "#DDEEFF"])
    assert p.colors[0] == "#aabbcc"
    assert len(p) == 6


def test_iteration_and_indexing():
    p = OceanPalette()
    assert list(p) == list(p.colors)
    assert p[0] == p.colors[0]


def test_as_list_returns_copy():
    p = OceanPalette()
    lst = p.as_list()
    lst[0] = "#000000"
    assert p.colors[0] != "#000000"


def test_random_color_is_member():
    p = SunsetPalette()
    for _ in range(20):
        assert p.random_color() in p.colors


def test_builtin_palettes_have_six_colors():
    for name, palette in PALETTES.items():
        assert len(palette) == 6
        assert palette.name == name
        for color in palette:
            assert color.startswith("#")
            assert len(color) == 7


def test_get_palette_case_insensitive():
    assert get_palette("OCEAN") == PALETTES["ocean"]
    assert isinstance(get_palette("midnight"), MidnightPalette)


def test_get_palette_unknown_raises():
    with pytest.raises(KeyError, match="Unknown palette"):
        get_palette("not-a-palette")


def test_midnight_matches_web_palette():
    web_colors = {
        "#60a5fa", "#34d399", "#a78bfa",
        "#f472b6", "#fbbf24", "#38bdf8",
    }
    assert set(MidnightPalette().colors) == web_colors


def test_subclasses_are_color_palette_instances():
    assert isinstance(BerryPalette(), ColorPalette)


def test_get_all_palettes_returns_ordered_list():
    palettes = get_all_palettes()
    assert len(palettes) == len(PALETTE_CLASSES)
    assert palettes[0]["name"] == "ocean"
    assert len(palettes[0]["colors"]) == 6
    assert "label" in palettes[0]
