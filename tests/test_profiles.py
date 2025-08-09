from gibberlink import freq_profile
import gibberlink
from gibberlink import decoder


def test_shared_freq_profile_reference():
    assert gibberlink.freq_profile is freq_profile
    assert decoder.freq_profile is freq_profile
    assert freq_profile(True, "streaming")[0] == 1500.0
    assert freq_profile(False, "studio")[3] == 3000.0
