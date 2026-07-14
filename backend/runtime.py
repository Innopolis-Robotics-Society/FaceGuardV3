"""Process settings that must be applied before application imports."""

import logging
import os


for thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(thread_variable, "1")


configured_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, configured_log_level, None)
if not isinstance(log_level, int):
    raise RuntimeError("LOG_LEVEL must be a valid Python logging level")
logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
