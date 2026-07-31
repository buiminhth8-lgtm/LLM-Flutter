from llm_studio.revisions.diff import TextDiffService


def test_revision_diff_identifies_equal_insert_and_delete():
    diff = TextDiffService().build_diff("keep\nold line", "keep\nnew line plus")

    types = [op["type"] for op in diff["ops"]]
    assert "equal" in types
    assert "delete" in types
    assert "insert" in types
    assert diff["summary"]["original_chars"] == len("keep\nold line")
    assert diff["summary"]["edited_chars"] == len("keep\nnew line plus")
    assert diff["summary"]["added_chars"] > 0
    assert diff["summary"]["removed_chars"] > 0
    assert diff["summary"]["changed_blocks"] >= 1


def test_revision_diff_is_stable_for_chinese_text():
    service = TextDiffService()
    first = service.build_diff("夜色沉入旧城。", "夜色沉入旧城，他没有后退。")
    second = service.build_diff("夜色沉入旧城。", "夜色沉入旧城，他没有后退。")

    assert first == second
    assert any(op["type"] == "insert" for op in first["ops"])
