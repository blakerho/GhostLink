import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from profiles import freq_profile
import GhostLink
import decoder


def test_shared_freq_profile_reference():
    assert GhostLink.freq_profile is freq_profile
    assert decoder.freq_profile is freq_profile
    assert freq_profile(True, "streaming")[0] == 1500.0
    assert freq_profile(False, "studio")[3] == 3000.0
