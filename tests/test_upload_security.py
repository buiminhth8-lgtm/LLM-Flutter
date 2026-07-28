import pytest

from llm_studio.security.uploads import (
    UploadExtensionNotAllowed,
    UploadFileTooLarge,
    UploadFilenameInvalid,
    UploadPolicy,
    sanitize_filename,
    save_upload_file_safely,
)


class FakeUploadFile:
    def __init__(self, filename: str, data: bytes, chunk_size: int = 2):
        self.filename = filename
        self._data = data
        self._offset = 0
        self._chunk_size = chunk_size
        self.read_sizes: list[int] = []
        self.closed = False

    async def read(self, size: int = -1):
        self.read_sizes.append(size)
        if self._offset >= len(self._data):
            return b""
        size = min(size, self._chunk_size)
        chunk = self._data[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    async def close(self):
        self.closed = True


def _policy(tmp_path, *, max_size=16):
    return UploadPolicy(
        max_size_bytes=max_size,
        allowed_extensions=(".txt",),
        allowed_mime_types=None,
        destination_dir=tmp_path,
    )


def test_sanitize_filename_rejects_path_traversal_and_reserved_names():
    with pytest.raises(UploadFilenameInvalid):
        sanitize_filename("../../config.yaml")
    with pytest.raises(UploadFilenameInvalid):
        sanitize_filename(r"C:\Windows\win.ini")
    with pytest.raises(UploadFilenameInvalid):
        sanitize_filename("CON.txt")


@pytest.mark.anyio
async def test_save_upload_file_safely_streams_and_uses_random_name(tmp_path):
    upload = FakeUploadFile("note.txt", b"hello world", chunk_size=3)

    saved = await save_upload_file_safely(upload, _policy(tmp_path))

    assert saved.original_filename == "note.txt"
    assert saved.path.name != "note.txt"
    assert saved.path.read_bytes() == b"hello world"
    assert upload.closed is True
    assert all(size == 1024 * 1024 for size in upload.read_sizes)


@pytest.mark.anyio
async def test_upload_extension_and_size_are_enforced(tmp_path):
    with pytest.raises(UploadExtensionNotAllowed):
        await save_upload_file_safely(FakeUploadFile("bad.exe", b"x"), _policy(tmp_path))

    with pytest.raises(UploadFileTooLarge):
        await save_upload_file_safely(FakeUploadFile("big.txt", b"0123456789", chunk_size=4), _policy(tmp_path, max_size=5))

    assert list(tmp_path.iterdir()) == []
