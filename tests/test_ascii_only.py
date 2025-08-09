from gibberlink.decoder import ascii_only


def test_ascii_only_strips_rtf_control_words():
    rtf = b"{\\rtf1\\ansi Bold \\b text\\b0 }"
    assert ascii_only(rtf) == "Bold text"


def test_ascii_only_drops_non_ascii():
    data = "Hi \u2665".encode("utf-8")
    assert ascii_only(data) == "Hi"
