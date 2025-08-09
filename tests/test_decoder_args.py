import sys
import pytest

from gibberlink import decoder


def test_parse_args_rejects_unknown_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["gibberlink-decode", "in.wav", "--amp"])
    with pytest.raises(SystemExit) as e:
        decoder.parse_args()
    assert e.value.code != 0
