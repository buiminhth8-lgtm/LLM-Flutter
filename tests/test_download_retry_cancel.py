import pytest

from llm_studio.jobs import Job, JobQueue, JobRepository, JobStatus, JobType
from llm_studio.jobs.exceptions import JobCancelNotAllowedError


def test_terminal_jobs_cannot_be_cancelled_and_keep_status(tmp_path):
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)

    for status in (
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.INTERRUPTED,
    ):
        job = Job.new(f"job-{status.value}", JobType.MODEL_DOWNLOAD.value, {}).with_update(
            status=status.value
        )
        repo.save(job)

        with pytest.raises(JobCancelNotAllowedError) as exc_info:
            queue.cancel(job.id)

        assert exc_info.value.error_code == "JOB_CANCEL_NOT_ALLOWED"
        assert repo.get(job.id).status == status.value


def test_pending_and_running_jobs_can_be_cancelled(tmp_path):
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)
    pending = Job.new("job-pending", JobType.MODEL_DOWNLOAD.value, {})
    running = Job.new("job-running", JobType.MODEL_DOWNLOAD.value, {}).with_update(
        status=JobStatus.RUNNING.value
    )
    repo.save(pending)
    repo.save(running)

    assert queue.cancel(pending.id).status == JobStatus.CANCELLING.value
    assert queue.cancel(running.id).status == JobStatus.CANCELLING.value
