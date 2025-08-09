import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import decoder


def test_parse_args_rejects_unknown_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["decoder.py", "in.wav", "--amp"])
    with pytest.raises(SystemExit) as e:
        decoder.parse_args()
    assert e.value.code != 0
