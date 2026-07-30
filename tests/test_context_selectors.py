from llm_studio.context.selectors import (
    CharacterSelector,
    PlotThreadSelector,
    PreviousChapterSelector,
    SceneSelector,
    TimelineSelector,
    WorldEntrySelector,
)


def test_character_selector_prioritizes_pov_and_main_characters():
    items = [
        {"id": "side", "name": "Side", "role": "support"},
        {"id": "main", "name": "Main", "role": "protagonist"},
        {"id": "pov", "name": "POV", "role": "support"},
    ]
    selected = CharacterSelector().select(items, pov_character_id="pov")
    assert [item["id"] for item in selected] == ["pov", "main", "side"]


def test_world_and_plot_selectors_apply_priority_rules():
    worlds = [
        {"id": "low", "title": "Low", "category": "other", "priority": 1},
        {"id": "high", "title": "High", "category": "world_rule", "priority": 90},
    ]
    assert WorldEntrySelector().select(worlds)[0]["id"] == "high"

    plots = [
        {"id": "done", "status": "resolved", "priority": 100},
        {"id": "open", "status": "open", "priority": 20},
        {"id": "active", "status": "in_progress", "priority": 10},
    ]
    assert [item["id"] for item in PlotThreadSelector().select(plots)] == [
        "active",
        "open",
    ]


def test_timeline_and_previous_chapter_selectors_use_current_chapter():
    events = [
        {"id": "old", "event_order": 1, "chapter_id": "c1"},
        {"id": "current", "event_order": 2, "chapter_id": "c2"},
        {"id": "future", "event_order": 3, "chapter_id": "c3"},
    ]
    selected = TimelineSelector().select(
        events,
        current_chapter_id="c2",
        current_chapter_index=2,
        chapter_indexes={"c1": 1, "c2": 2, "c3": 3},
    )
    assert [item["id"] for item in selected] == ["old", "current"]

    chapters = [
        {"id": "c1", "chapter_index": 1, "summary": "previous summary"},
        {"id": "c2", "chapter_index": 2, "summary": ""},
    ]
    previous, summary, warnings = PreviousChapterSelector().select(
        chapters,
        chapters[1],
    )
    assert previous["id"] == "c1"
    assert summary == "previous summary"
    assert warnings == []


def test_scene_selector_uses_explicit_scene_id():
    scenes = [{"id": "s1"}, {"id": "s2"}]
    assert SceneSelector().select(scenes, "s2") == {"id": "s2"}
    assert SceneSelector().select(scenes, None) is None
