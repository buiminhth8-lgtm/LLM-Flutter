from llm_studio.context.assembler import ContextAssembler


def _request(**changes):
    data = {
        "mode": "chapter_generate",
        "target_budget": {
            "max_tokens": 4096,
            "reserved_output_tokens": 1200,
            "max_context_tokens": 2500,
            "max_chars": 12000,
            "hard_limit": True,
        },
        "user_variables": {"current_chapter_goal": "Enter the market"},
        "include": {},
    }
    data.update(changes)
    return data


def _assemble(request):
    return ContextAssembler().assemble(
        project={
            "id": "p1",
            "title": "Night",
            "genre": "fantasy",
            "description": "project description",
            "target_style": "restrained",
            "target_audience": "adult",
        },
        chapter={
            "id": "c2",
            "chapter_index": 2,
            "title": "Market",
            "outline": "Find the trader",
            "summary": "",
            "status": "outline",
        },
        scene={
            "id": "s1",
            "title": "Gate",
            "outline": "Enter",
            "pov_character_id": "hero",
            "location": "Black Market",
            "timeline_note": "midnight",
        },
        chapters=[
            {
                "id": "c1",
                "chapter_index": 1,
                "title": "Before",
                "summary": "Arrived in the city",
            },
            {"id": "c2", "chapter_index": 2, "title": "Market"},
        ],
        characters=[
            {
                "id": "hero",
                "name": "Lin",
                "role": "protagonist",
                "personality": "calm",
                "goals": "truth",
                "speech_style": "brief",
            }
        ],
        world_entries=[
            {
                "id": f"w{index}",
                "title": f"World {index}",
                "category": "other",
                "content": "x" * 200,
                "priority": index,
            }
            for index in range(5)
        ],
        plot_threads=[
            {
                "id": "plot",
                "title": "Trade",
                "description": "Find the source",
                "status": "open",
                "priority": 10,
                "related_character_ids": '["hero"]',
            }
        ],
        timeline_events=[
            {
                "id": "event",
                "title": "Token",
                "event_order": 1,
                "chapter_id": "c1",
                "description": "Found a token",
            }
        ],
        request=request,
    )


def test_context_assembler_builds_standard_variables_and_user_overrides():
    result = _assemble(
        _request(user_variables={"chapter_title": "Override", "pov": "third"})
    )

    assert result.variables["project_title"] == "Night"
    assert result.variables["chapter_title"] == "Override"
    assert result.variables["pov"] == "third"
    assert "【人物】" in result.variables["characters"]
    assert result.selected_items["characters"] == ["hero"]
    assert result.context_hash


def test_context_assembler_truncates_low_priority_material_first():
    result = _assemble(
        _request(
            target_budget={
                "max_tokens": 300,
                "reserved_output_tokens": 100,
                "max_context_tokens": 100,
                "max_chars": 600,
                "hard_limit": True,
            }
        )
    )

    truncated = [warning for warning in result.warnings if warning["code"] == "CONTEXT_TRUNCATED"]
    assert truncated
    assert "world_entries" in truncated[0]["affected"]
    assert result.variables["current_chapter_goal"] == "Enter the market"


def test_context_assembler_never_truncates_user_overrides():
    result = _assemble(
        _request(
            target_budget={
                "max_tokens": 100,
                "reserved_output_tokens": 20,
                "max_context_tokens": 40,
                "max_chars": 80,
                "hard_limit": True,
            },
            user_variables={
                "current_chapter_goal": "protected goal",
                "world_setting": "user supplied world " * 20,
            },
        )
    )

    assert result.variables["current_chapter_goal"] == "protected goal"
    assert result.variables["world_setting"].startswith("user supplied world")
    assert any(
        warning["code"] == "CONTEXT_BUDGET_EXCEEDED"
        for warning in result.warnings
    )
