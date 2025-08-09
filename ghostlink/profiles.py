"""Shared frequency profiles for Gibberlink encoder/decoder."""

from typing import List


def freq_profile(dense: bool, profile: str) -> List[float]:
    """Return carrier frequencies for the given profile.

    Profiles are chosen to survive typical consumer gear and lossy codecs.
    """
    if profile not in ("streaming", "studio"):
        raise ValueError("mix-profile must be 'streaming' or 'studio'")
    if dense:
        # 8-FSK, equal-ish spacing; steer clear of sub-1k mud and >6k rolloff
        return [1500.0, 1900.0, 2300.0, 2700.0, 3100.0, 3500.0, 3900.0, 4300.0] if profile == "streaming" \
            else [1800.0, 2200.0, 2600.0, 3000.0, 3400.0, 3800.0, 4200.0, 4600.0]
    # 4-FSK
    return [1600.0, 2100.0, 2700.0, 3300.0] if profile == "streaming" \
        else [1800.0, 2200.0, 2600.0, 3000.0]
