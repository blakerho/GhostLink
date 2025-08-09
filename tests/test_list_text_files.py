from ghostlink import list_text_files

def test_list_text_files_returns_sorted_paths(tmp_path):
    names = ["b.txt", "a.txt", "c.md", "d.log", "ignore.bin"]
    for name in names:
        (tmp_path / name).write_text("data")

    result = list_text_files(str(tmp_path))
    expected = sorted(str(tmp_path / n) for n in ["a.txt", "b.txt", "c.md", "d.log"])
    assert result == list(expected)
