"""Shared frequency profiles for Gibberlink encoder/decoder."""

from typing import List


def freq_profile(dense: bool, profile: str) -> List[float]:
    """Return carrier frequencies for the given profile.

    Profiles are chosen to survive typical consumer gear and lossy codecs.
    """
    if profile not in ("streaming", "studio"):
        raise ValueError("mix-profile must be 'streaming' or 'studio'")
    if dense:
        # 8-FSK carriers from Gibberlink spec
        return [
            1500.0,
            2000.0,
            2500.0,
            3000.0,
            3500.0,
            4000.0,
            4500.0,
            5000.0,
        ] if profile == "streaming" else [
            1800.0,
            2400.0,
            3000.0,
            3600.0,
            4200.0,
            4800.0,
            5400.0,
            6000.0,
        ]
    # 4-FSK carriers from Gibberlink spec
    return [
        1750.0,
        2750.0,
        3750.0,
        4750.0,
    ] if profile == "streaming" else [
        2100.0,
        3300.0,
        4500.0,
        5700.0,
    ]
