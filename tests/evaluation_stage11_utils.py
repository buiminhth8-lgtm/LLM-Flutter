from __future__ import annotations

import asyncio
from types import SimpleNamespace

from llm_studio.evaluation import EvaluationService
from llm_studio.jobs import JobQueue, JobRepository
from llm_studio.novels import NovelService


def make_project(novels: NovelService):
    project = novels.create_project(
        {
            "title": "Stage 11",
            "target_style": "紧张 压迫 细节",
        }
    )
    chapter = novels.create_chapter(
        project["id"],
        {
            "title": "黑市",
            "draft_content": "林烬进入黑市，发现灵骨交易。林烬说我要查清真相。",
            "summary": "林烬进入黑市发现灵骨交易",
        },
    )
    novels.create_character(
        project["id"],
        {"name": "林烬", "speech_style": "克制", "goals": "查清父亲死因"},
    )
    novels.create_world_entry(
        project["id"],
        {"category": "rule", "title": "黑市规则", "content": "黑市禁止灵火"},
    )
    novels.create_world_entry(
        project["id"],
        {"category": "foreshadowing", "title": "骨片印记", "content": "未来回收"},
    )
    novels.create_plot_thread(
        project["id"],
        {"title": "灵骨交易", "description": "主线索仍未解决", "status": "open"},
    )
    novels.create_timeline_event(project["id"], {"title": "父亲失踪", "description": "旧案线索"})
    return project, chapter


def make_evaluation_service(tmp_path, *, job_queue: bool = False) -> EvaluationService:
    db = tmp_path / "novels.sqlite"
    novels = NovelService(db)
    queue = None
    if job_queue:
        queue = JobQueue(JobRepository(tmp_path / "jobs.sqlite"))
    return EvaluationService(db, novel_service=novels, job_queue=queue)


class FakeRuntimeBridge:
    async def generate_text(self, **kwargs):
        return SimpleNamespace(
            text='{"overall_score":4,"summary":"本地评估完成","findings":[{"severity":"info","category":"style","title":"ok","message":"ok"}]}'
        )


def run(coro):
    return asyncio.run(coro)

