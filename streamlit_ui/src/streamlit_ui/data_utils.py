"""I/O helpers — CSV ingest + the per-run output sink.

Every Streamlit interaction that produces tables or plots calls
``new_run_dir()`` once, then drops every CSV and PNG into that one folder.
That keeps stakeholder review trivial: one folder per session, files are
co-located, and download buttons in the UI map to the same files.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

import pandas as pd

from streamlit_ui.config import get_settings
from streamlit_ui.logging_config import get_logger

logger = get_logger(__name__)


def new_run_dir(prefix: str = "run") -> Path:
    """Create a unique, timestamped output directory and return it."""
    s = get_settings()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = s.output_dir / f"{prefix}_{stamp}"
    path.mkdir(parents=True, exist_ok=True)
    logger.info("run_dir_created", path=str(path))
    return path


def save_dataframe(df: pd.DataFrame, run_dir: Path, name: str) -> Path:
    """Persist a DataFrame as CSV inside the run folder. Returns the path."""
    if not name.endswith(".csv"):
        name = f"{name}.csv"
    path = run_dir / name
    df.to_csv(path, index=False)
    logger.info("dataframe_saved", path=str(path), rows=len(df))
    return path


def read_uploaded_csv(file_like: IO[bytes] | None) -> pd.DataFrame:
    """Read a Streamlit ``file_uploader`` result into a DataFrame.

    Raises
    ------
    ValueError
        When the upload is missing or unparseable.
    """
    if file_like is None:
        raise ValueError("No file uploaded.")
    raw = file_like.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not parse the CSV: {exc}") from exc
    logger.info("csv_uploaded", rows=len(df), cols=df.columns.tolist())
    return df


def parse_loyalty_ids(text: str) -> list[int]:
    """Parse a free-text list of loyalty IDs (commas / spaces / newlines)."""
    if not text:
        return []
    tokens = [
        t.strip() for t in text.replace(";", ",").replace("\n", ",").split(",")
    ]
    ids: list[int] = []
    bad: list[str] = []
    for t in tokens:
        if not t:
            continue
        try:
            ids.append(int(t))
        except ValueError:
            bad.append(t)
    if bad:
        raise ValueError(f"Not numeric: {bad[:5]}")
    return ids


def extract_id_column(df: pd.DataFrame) -> list[int]:
    """Find a loyalty_number column in any reasonable spelling and return ids."""
    for cand in ("loyalty_number", "loyalty_id", "id", "customer_id"):
        if cand in df.columns:
            return df[cand].astype(int).tolist()
    raise ValueError(
        "Could not find a loyalty_number column. "
        "Accepted aliases: loyalty_number, loyalty_id, id, customer_id."
    )
