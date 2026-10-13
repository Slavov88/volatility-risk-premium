"""One authorized official archival CLOSE insertion; never a generic fill."""
from __future__ import annotations

import hashlib
import json
from io import StringIO
from pathlib import Path

import pandas as pd

from vrp.processed_panel import PanelProvenanceError, _verified_artifact

AMENDMENT = "2026-10-13-interim-vix-close/1.0.0"
TRANSFORMATION = "official-cboe-archival-insertion/1.0.0"
ARCHIVE_URL = "https://cdn.cboe.com/resources/us/indices/vixarchive.xls"
ARCHIVE_SHA = "9f618c4d69c5ec784705c7a401382a6e066fde87d22bf893bfcd306132b03566"
INSERT_DATE = "1999-12-31"
INSERT_CLOSE = 24.64
AUTHORIZATION = {
    "amendment": AMENDMENT,
    "status": "AUTHORIZED_AS_REPORTED_BY_ALEKSANDAR",
    "communicated_on": "2026-10-13",
    "reported_by": "Aleksandar Slavov",
    "authors": ["Aleksandar Slavov", "Venelin Mirchev"],
    "independently_verified_signatures": False,
    "independent_freeze_acceptance": "PENDING",
    "allowed_insertions": [{"date": INSERT_DATE, "close": INSERT_CLOSE}],
}


def verify_archive(raw_root: Path, descriptor: dict) -> dict:
    """Hash original XLS bytes and read the bound date and numeric cells."""
    if descriptor.get("source_url") != ARCHIVE_URL or descriptor.get("sha256") != ARCHIVE_SHA:
        raise PanelProvenanceError("Archive source identity/SHA-256 contract mismatch")
    raw = _verified_artifact(raw_root.resolve(), descriptor, "Cboe XLS archive")
    try:
        import xlrd
    except ImportError as error:
        raise PanelProvenanceError("Use isolated xlrd==2.0.2 via --parser-path") from error
    if xlrd.__version__ != "2.0.2":
        raise PanelProvenanceError("Archive parser must be xlrd==2.0.2")
    book = xlrd.open_workbook(file_contents=raw)
    sheet = book.sheet_by_name("OHLC")
    if book.datemode != 0 or sheet.row_values(1) != ["Date", "VIX Open", "VIX High", "VIX Low", "VIX Close"]:
        raise PanelProvenanceError("Archive date system/schema mismatch")
    days = [xlrd.xldate_as_datetime(sheet.cell_value(i, 0), book.datemode).date().isoformat()
            for i in range(2, sheet.nrows)]
    if len(days) != len(set(days)):
        raise PanelProvenanceError("Duplicate archive dates")
    row = 2527  # XLS row 2528, verified against the pinned original artifact.
    if days[row - 2] != INSERT_DATE or sheet.cell_value(row, 0) != 36525.0:
        raise PanelProvenanceError("Archive bound date/cell mismatch")
    close = sheet.cell_value(row, 4)
    if sheet.cell_type(row, 4) != xlrd.XL_CELL_NUMBER or close != INSERT_CLOSE:
        raise PanelProvenanceError("Archive numeric CLOSE mismatch")
    low, high = sheet.cell_value(row, 3), sheet.cell_value(row, 2)
    if not 0 < low <= close <= high:
        raise PanelProvenanceError("Archive CLOSE/range mismatch")
    return {"date": INSERT_DATE, "close": float(close), "unit": "annualized percentage points",
        "source_url": ARCHIVE_URL, "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "sheet": "OHLC", "row_one_based": row + 1, "date_cell": "A2528",
        "close_cell": "E2528", "date_serial": 36525.0, "excel_datemode": 0,
        "parser": "xlrd==2.0.2", "numeric_cell_verified": True,
        "original_csv_absent": True, "reason": "official archival-source insertion; original CSV omission",
        "transformation_version": TRANSFORMATION, "verification": "TECHNICALLY_VERIFIED",
        "independent_review": "PENDING"}


def insert_archival_close(source: pd.DataFrame, evidence: dict, authorization: dict) -> pd.DataFrame:
    """Require the exact communicated contract and original absence."""
    if authorization != AUTHORIZATION:
        raise PanelProvenanceError("Unauthorized archival insertion metadata")
    expected = {"date": INSERT_DATE, "close": INSERT_CLOSE, "source_url": ARCHIVE_URL,
        "artifact_sha256": ARCHIVE_SHA, "unit": "annualized percentage points",
        "sheet": "OHLC", "date_cell": "A2528", "close_cell": "E2528",
        "numeric_cell_verified": True, "transformation_version": TRANSFORMATION}
    if any(evidence.get(k) != v for k, v in expected.items()):
        raise PanelProvenanceError("Archival insertion evidence mismatch")
    if source.Date.duplicated().any():
        raise PanelProvenanceError("Duplicate original CLOSE dates")
    if INSERT_DATE in set(source.Date):
        raise PanelProvenanceError("Original/archival date collision: insertion requires absence")
    result = source[["Date", "CLOSE"]].copy()
    result["vix_source"] = "cboe_csv"
    result = pd.concat([result, pd.DataFrame([{"Date": INSERT_DATE, "CLOSE": INSERT_CLOSE,
        "vix_source": "cboe_xls_archival_insertion"}])], ignore_index=True)
    return result.sort_values("Date", kind="stable").reset_index(drop=True)


def verify_fred_corroboration(root: Path, descriptor: dict) -> dict:
    expected_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd=1999-12-30&coed=2000-01-03"
    if (descriptor.get("source_url") != expected_url or descriptor.get("sha256") !=
            "cf5fd219cd8cd428b287c6f260baaefd746e11ca8ef1eb19ffc9741204d58bcb"):
        raise PanelProvenanceError("FRED corroboration identity mismatch")
    raw = _verified_artifact(root.resolve(), descriptor, "FRED VIXCLS corroboration")
    data = pd.read_csv(StringIO(raw.decode()), dtype={"observation_date": str})
    matches = data.loc[data.observation_date == INSERT_DATE, "VIXCLS"]
    if len(matches) != 1 or float(matches.iloc[0]) != INSERT_CLOSE:
        raise PanelProvenanceError("FRED corroborating CLOSE mismatch")
    return {"date": INSERT_DATE, "same_value_verified": True,
        "source_url": expected_url, "sha256": descriptor["sha256"],
        "role": "Cboe-sourced republication; not independent index calculation"}
