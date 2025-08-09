import logging

import pytest

from gibberlink import iter_inputs, read_utf8_bytes


def test_iter_inputs_skips_unreadable_files(tmp_path, monkeypatch, caplog):
    good = tmp_path / "good.txt"
    good.write_text("ok")
    bad = tmp_path / "bad.txt"
    bad.write_text("bad")

    def fake_read(src, is_literal):
        if src == str(bad):
            raise OSError("boom")
        return read_utf8_bytes(src, is_literal)

    monkeypatch.setattr("gibberlink.__main__.read_utf8_bytes", fake_read)

    with caplog.at_level(logging.ERROR):
        result = list(iter_inputs("dir", str(tmp_path)))

    assert [(name, data) for name, data in result] == [("good.txt", b"ok")]
    assert "Skipping" in caplog.text


def test_iter_inputs_processes_malformed_utf8(tmp_path, caplog):
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"\xff\xfe")

    with caplog.at_level(logging.WARNING):
        result = list(iter_inputs("dir", str(tmp_path)))

    assert result == [("bad.txt", b"\xff\xfe")]
    assert "not valid UTF-8" in caplog.text

