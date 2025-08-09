from gibberlink import freq_profile
import gibberlink
from gibberlink import decoder


def test_shared_freq_profile_reference():
    assert gibberlink.freq_profile is freq_profile
    assert decoder.freq_profile is freq_profile
    streaming_dense = freq_profile(True, "streaming")
    assert streaming_dense == [
        1500.0,
        2000.0,
        2500.0,
        3000.0,
        3500.0,
        4000.0,
        4500.0,
        5000.0,
    ]
    studio_sparse = freq_profile(False, "studio")
    assert studio_sparse == [2100.0, 3300.0, 4500.0, 5700.0]
