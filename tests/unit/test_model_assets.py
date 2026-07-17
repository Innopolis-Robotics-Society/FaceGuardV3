import io
import zipfile

import pytest

import model_assets


def model_zip(*, corrupt=False):
    if corrupt:
        return b"not-a-zip"
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        archive.writestr("buffalo_s/det_500m.onnx", b"detector")
        archive.writestr("buffalo_s/w600k_mbf.onnx", b"recognizer")
    return result.getvalue()


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.headers = {"content-length": str(len(payload))}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, chunk_size):
        payload, self.payload = self.payload, b""
        return payload


def test_model_bootstrap_downloads_validates_and_reuses_cache(tmp_path, monkeypatch):
    def open_model(*args, **kwargs):
        return FakeResponse(model_zip())

    monkeypatch.setattr(model_assets, "urlopen", open_model)

    model_dir = model_assets.ensure_buffalo_s_model(tmp_path)
    assert (model_dir / "det_500m.onnx").read_bytes() == b"detector"
    assert (model_dir / "w600k_mbf.onnx").read_bytes() == b"recognizer"

    monkeypatch.setattr(
        model_assets,
        "urlopen",
        lambda *args, **kwargs: pytest.fail("complete cache must be reused"),
    )
    assert model_assets.ensure_buffalo_s_model(tmp_path) == model_dir


def test_model_bootstrap_reports_corrupt_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(
        model_assets,
        "urlopen",
        lambda *args, **kwargs: FakeResponse(model_zip(corrupt=True)),
    )

    with pytest.raises(model_assets.ModelAssetError, match="valid ZIP"):
        model_assets.ensure_buffalo_s_model(tmp_path)


def test_model_download_retries_bounded_network_failures(tmp_path, monkeypatch):
    attempts = []

    def fail(*args, **kwargs):
        attempts.append(1)
        raise TimeoutError("network stalled")

    monkeypatch.setattr(model_assets, "urlopen", fail)
    monkeypatch.setattr(model_assets.time, "sleep", lambda delay: None)

    with pytest.raises(model_assets.ModelAssetError, match="after 3 attempts"):
        model_assets.ensure_buffalo_s_model(tmp_path)
    assert len(attempts) == 3
