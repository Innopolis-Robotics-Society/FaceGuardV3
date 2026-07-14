"""Reliable bootstrap for InsightFace assets stored in the Docker model cache."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen
import zipfile


logger = logging.getLogger(__name__)

DEFAULT_INSIGHTFACE_ROOT = "/root/.insightface"
BUFFALO_S_URL = (
    "https://github.com/deepinsight/insightface/releases/download/" "v0.7/buffalo_s.zip"
)
BUFFALO_S_REQUIRED_FILES = {"det_500m.onnx", "w600k_mbf.onnx"}


class ModelAssetError(RuntimeError):
    """Raised when required recognition assets cannot be prepared safely."""


def _has_required_files(model_dir: Path, required_files: set[str]) -> bool:
    return all((model_dir / filename).is_file() for filename in required_files)


def _download_archive(url: str, archive_path: Path, attempts: int = 3) -> None:
    for attempt in range(1, attempts + 1):
        try:
            # The default is a fixed vendor HTTPS endpoint; an override is an
            # explicit operator-controlled deployment setting.
            with urlopen(url, timeout=30) as response:  # nosec B310
                expected_size = response.headers.get("content-length")
                written = 0
                next_report = 16 * 1024 * 1024
                with archive_path.open("wb") as destination:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        destination.write(chunk)
                        written += len(chunk)
                        if written >= next_report:
                            logger.info(
                                "InsightFace model download progress: %.1f MiB",
                                written / (1024 * 1024),
                            )
                            next_report += 16 * 1024 * 1024
                if expected_size is not None and written != int(expected_size):
                    raise URLError(
                        "Incomplete model download: "
                        f"expected {expected_size} bytes, received {written}"
                    )
                return
        except (TimeoutError, URLError) as error:
            archive_path.unlink(missing_ok=True)
            if attempt == attempts:
                raise ModelAssetError(
                    f"Unable to download InsightFace model after {attempts} attempts"
                ) from error
            delay = float(attempt)
            logger.warning(
                "InsightFace model download attempt %s/%s failed; retrying in %.0fs",
                attempt,
                attempts,
                delay,
            )
            time.sleep(delay)


def _safe_extract_model(
    archive_path: Path,
    models_dir: Path,
    model_name: str,
    required_files: set[str],
) -> None:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            corrupt_member = archive.testzip()
            if corrupt_member is not None:
                raise ModelAssetError(
                    f"InsightFace model archive is corrupt at {corrupt_member!r}"
                )
            with tempfile.TemporaryDirectory(
                prefix=f".{model_name}-extract-", dir=models_dir
            ) as extract_directory:
                extract_root = Path(extract_directory).resolve()
                for member in archive.infolist():
                    destination = (extract_root / member.filename).resolve()
                    if (
                        extract_root not in destination.parents
                        and destination != extract_root
                    ):
                        raise ModelAssetError(
                            "InsightFace model archive contains an unsafe path"
                        )
                archive.extractall(extract_root)

                candidates = [extract_root / model_name, extract_root]
                source = next(
                    (
                        candidate
                        for candidate in candidates
                        if _has_required_files(candidate, required_files)
                    ),
                    None,
                )
                if source is None:
                    raise ModelAssetError(
                        "InsightFace model archive is missing required ONNX files"
                    )

                target = models_dir / model_name
                target.mkdir(parents=True, exist_ok=True)
                for item in source.iterdir():
                    destination = target / item.name
                    if item.is_dir():
                        if destination.exists():
                            shutil.rmtree(destination)
                        shutil.move(str(item), str(destination))
                    else:
                        os.replace(item, destination)
    except zipfile.BadZipFile as error:
        raise ModelAssetError(
            "InsightFace model archive is not a valid ZIP; check storage/media health"
        ) from error


def ensure_buffalo_s_model(root: str | Path | None = None) -> Path:
    """Download, validate and atomically populate the persisted model cache."""
    insightface_root = Path(
        root or os.environ.get("INSIGHTFACE_ROOT", DEFAULT_INSIGHTFACE_ROOT)
    ).expanduser()
    models_dir = insightface_root / "models"
    model_dir = models_dir / "buffalo_s"
    if _has_required_files(model_dir, BUFFALO_S_REQUIRED_FILES):
        return model_dir

    models_dir.mkdir(parents=True, exist_ok=True)
    # This exact cache path is gitignored. If the process is killed during the
    # first download, the next attempt truncates and replaces the partial file.
    archive_path = models_dir / "buffalo_s.zip"
    model_url = os.environ.get("INSIGHTFACE_MODEL_URL", BUFFALO_S_URL)
    logger.info("InsightFace buffalo_s model is absent; downloading it once")
    try:
        _download_archive(model_url, archive_path)
        _safe_extract_model(
            archive_path,
            models_dir,
            "buffalo_s",
            BUFFALO_S_REQUIRED_FILES,
        )
    finally:
        archive_path.unlink(missing_ok=True)

    if not _has_required_files(model_dir, BUFFALO_S_REQUIRED_FILES):
        raise ModelAssetError("InsightFace buffalo_s model bootstrap did not complete")
    logger.info("InsightFace buffalo_s model cache is ready")
    return model_dir
