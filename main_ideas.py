#!/usr/bin/env python3
"""
main_ideas.py

Minimal script to fetch "ideas" (ticket/kickbox data) from two endpoints and save to CSV and Excel.

Usage:
    1) Edit TOKEN in this file (hardcoded) to your Bearer token.
    2) Optionally adjust date range and limits in the CONFIG section below.
    3) Run:
        python3 main_ideas.py

Produces:
 - ideas.csv
 - ideas.xlsx

Dependencies:
    pip install requests pandas openpyxl
"""

from __future__ import annotations
import copy
import json
import sys
from itertools import islice
from typing import Any, Dict, List

import pandas as pd
import requests

# ----------------- CONFIG (edit as needed) -----------------
# Put your token here (hardcoded for one-command run)
TOKEN = "eyJraWQiOiIxIiwiYWxnIjoiRWREU0EifQ.eyJpc3MiOiJraWNrYm94LWltcHJvdmUiLCJzdWIiOiJhNjE0ZWZjOC0zMmI4LTRjYjItYjgwYi1iYzRiZDAxOGVkOWQiLCJhdWQiOiJQQVNIQUhvbGRpbmciLCJjb250ZXh0cyI6WyJQQVNIQUhvbGRpbmciXSwiZXhwIjoxNzYwNjc3Mjg1fQ.GXMVeQ8gFXvzsV97V_NQ5adDW27AN-CmHFHbeIsoArKU4UoeXAc8RQnInoK_a_hjgJJ7PoJLCiae5ZGlMC6IDQ"  
# <-- Replace with your bearer token string

SEARCH_URL = "https://api.rready.com/PASHAHolding/global-search/ticket-attachment"
FETCH_BY_CANONICAL_BATCH_URL = "https://api.rready.com/PASHAHolding/ticket/kickbox/fetchByCanonicalIdByBatch"

# Date filters in payload (example range you used). Edit to desired range.
DATE_FROM = "2018-01-01T00:00:00.000Z"
DATE_TO = "2025-09-17T23:59:59.999Z"

# Try a larger single-request limit first
MAX_SINGLE_LIMIT = 2000

# Per-page size when doing pagination strategies
PAGINATION_LIMIT = 1000

# Safety cap to avoid accidentally fetching gigantic datasets
SAFE_TOTAL_CAP = 20000

# How many canonical IDs to send per fetchByCanonicalIdByBatch call
BATCH_SIZE = 100

# Output files
CSV_OUTPUT = "ideas.csv"
XLSX_OUTPUT = "ideas.xlsx"
# ----------------------------------------------------------

def chunked_iterable(iterable, size):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk

def flatten_dict(d: Dict[str, Any], parent: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        key = f"{parent}.{k}" if parent else k
        if isinstance(v, dict):
            out.update(flatten_dict(v, key))
        else:
            out[key] = v
    return out

def normalize_ideas(ideas: List[Dict]) -> pd.DataFrame:
    """
    Flatten idea objects into a pandas DataFrame:
     - nested dicts -> dot notation
     - simple lists -> comma-joined strings
     - complex lists -> json.dumps into a single cell
    """
    rows = []
    keys = set()
    for idea in ideas:
        flat: Dict[str, Any] = {}
        for k, v in idea.items():
            if isinstance(v, dict):
                flat.update(flatten_dict(v, parent=k))
            elif isinstance(v, list):
                if all(not isinstance(x, (dict, list)) for x in v):
                    flat[k] = ", ".join(str(x) for x in v)
                else:
                    try:
                        flat[k] = json.dumps(v, ensure_ascii=False)
                    except Exception:
                        flat[k] = str(v)
            else:
                flat[k] = v
        rows.append(flat)
        keys.update(flat.keys())

    preferred = ["id", "canonicalId", "title", "status", "type", "createdDate", "creator"]
    rest = sorted(k for k in keys if k not in preferred)
    ordered = [k for k in preferred if k in keys] + rest

    df = pd.DataFrame([{k: r.get(k, "") for k in ordered} for r in rows])
    return df

def try_post(session: requests.Session, url: str, payload: Dict, timeout: int = 30):
    try:
        resp = session.post(url, json=payload, timeout=timeout)
    except Exception as e:
        print(f"Network error when calling {url}: {e}")
        return None
    return resp

def extract_canonical_ids_from_search_response(resp_json: Any) -> List[str]:
    """
    Given the JSON returned by the ticket-attachment search endpoint, extract ticketCanonicalId values.
    The example you provided is an array like:
      [ {"ticketCanonicalId":"PASHAHolding-kickbox-1950", "index":"ticket"}, ... ]
    """
    out: List[str] = []
    if isinstance(resp_json, list):
        for el in resp_json:
            if isinstance(el, dict):
                val = el.get("ticketCanonicalId") or el.get("canonicalId") or el.get("id")
                if isinstance(val, str) and val.strip():
                    out.append(val)
    elif isinstance(resp_json, dict):
        # sometimes the endpoint could return object with hits/hits structure; try common paths
        # e.g. {"hits": {"hits": [{...}, {...}]}}
        maybe_hits = resp_json.get("hits")
        if isinstance(maybe_hits, dict):
            inner = maybe_hits.get("hits")
            if isinstance(inner, list):
                for it in inner:
                    if isinstance(it, dict):
                        # try multiple paths
                        val = it.get("_source", {}).get("ticketCanonicalId") or it.get("_source", {}).get("canonicalId")
                        if not val:
                            val = it.get("ticketCanonicalId") or it.get("canonicalId")
                        if isinstance(val, str) and val.strip():
                            out.append(val)
    return out

def dedupe_preserve_order(seq: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def fetch_canonical_ids_smart(session: requests.Session, base_payload: Dict) -> List[str]:
    """
    Try fetching canonical IDs using a large single request first, and then several pagination strategies if needed.
    Returns a deduplicated list of canonical IDs (strings).
    """
    collected: List[str] = []

    payload_single = copy.deepcopy(base_payload)
    payload_single["limit"] = MAX_SINGLE_LIMIT
    print(f"Attempting single search request with limit={MAX_SINGLE_LIMIT} ...")
    resp = try_post(session, SEARCH_URL, payload_single)
    if resp is None:
        sys.exit(2)
    if resp.status_code == 401:
        print("Unauthorized (401). Token invalid or expired.")
        sys.exit(3)
    if resp.status_code != 200:
        print(f"Search endpoint returned {resp.status_code}: {resp.text[:300]}")
        sys.exit(4)

    try:
        data = resp.json()
    except Exception as e:
        print("Failed to parse JSON from search response:", e)
        sys.exit(5)

    first_batch = extract_canonical_ids_from_search_response(data)
    collected.extend(first_batch)
    print(f"Single request returned {len(first_batch)} canonical IDs.")

    # If less than the requested limit — assume complete.
    if len(first_batch) < MAX_SINGLE_LIMIT:
        print("Less than limit returned — assuming complete list.")
        return dedupe_preserve_order(collected)

    # Try several pagination strategies because equal-to-limit suggests more data exists.
    print("Response size equals requested limit — trying pagination strategies...")

    # Strategy A: offset-like keys
    offset_keys = ["offset", "start", "from"]
    for key in offset_keys:
        print(f"Trying offset-style pagination with key='{key}', page_size={PAGINATION_LIMIT} ...")
        items = list(collected)
        offset = len(first_batch)
        while True:
            if len(items) >= SAFE_TOTAL_CAP:
                print(f"Reached safe cap {SAFE_TOTAL_CAP}; stopping offset pagination.")
                break
            page_payload = copy.deepcopy(base_payload)
            page_payload["limit"] = PAGINATION_LIMIT
            page_payload[key] = offset
            resp_page = try_post(session, SEARCH_URL, page_payload)
            if resp_page is None or resp_page.status_code != 200:
                print(f"Offset pagination with key={key} stopped (HTTP status or network).")
                break
            try:
                page_json = resp_page.json()
            except Exception:
                print("Failed to parse JSON during offset pagination.")
                break
            page_ids = extract_canonical_ids_from_search_response(page_json)
            if not page_ids:
                print(f"No more results for offset key '{key}'.")
                break
            items.extend(page_ids)
            print(f"  got {len(page_ids)} canonical IDs (total collected {len(items)})")
            if len(page_ids) < PAGINATION_LIMIT:
                print("  Last page smaller than page_size -> finishing offset pagination.")
                break
            offset += len(page_ids)
        if len(items) > len(collected):
            print(f"Offset-style pagination with key='{key}' retrieved additional canonical IDs (total {len(items)}).")
            collected = items
            return dedupe_preserve_order(collected)
        else:
            print(f"No extra canonical IDs found using key='{key}'. Trying next strategy...")

    # Strategy B: page-based pagination (page + size)
    print("Trying page-based pagination (page + size / page + limit)...")
    for size_key in ["size", "limit"]:
        for start_page in (0, 1):
            items = list(collected)
            page = start_page
            while True:
                if len(items) >= SAFE_TOTAL_CAP:
                    print(f"Reached safe cap {SAFE_TOTAL_CAP}; stopping page-based pagination.")
                    break
                page_payload = copy.deepcopy(base_payload)
                page_payload[size_key] = PAGINATION_LIMIT
                page_payload["page"] = page
                resp_page = try_post(session, SEARCH_URL, page_payload)
                if resp_page is None or resp_page.status_code != 200:
                    break
                try:
                    page_json = resp_page.json()
                except Exception:
                    break
                page_ids = extract_canonical_ids_from_search_response(page_json)
                if not page_ids:
                    break
                items.extend(page_ids)
                print(f"  page {page} got {len(page_ids)} canonical IDs (total {len(items)})")
                if len(page_ids) < PAGINATION_LIMIT:
                    break
                page += 1
            if len(items) > len(collected):
                print(f"Page-based pagination (start_page {start_page}, size_key '{size_key}') retrieved extra canonical IDs (total {len(items)})")
                collected = items
                return dedupe_preserve_order(collected)

    # Last-resort: bigger single limit (bounded)
    LAST_RESORT_LIMIT = min(5000, SAFE_TOTAL_CAP)
    if LAST_RESORT_LIMIT > MAX_SINGLE_LIMIT:
        print(f"Last resort: trying larger single request limit={LAST_RESORT_LIMIT} ...")
        payload_last = copy.deepcopy(base_payload)
        payload_last["limit"] = LAST_RESORT_LIMIT
        resp_last = try_post(session, SEARCH_URL, payload_last)
        if resp_last and resp_last.status_code == 200:
            try:
                last_json = resp_last.json()
                last_ids = extract_canonical_ids_from_search_response(last_json)
                if isinstance(last_ids, list) and len(last_ids) > len(collected):
                    collected = last_ids
                    print(f"Last-resort request returned {len(collected)} canonical IDs.")
                    return dedupe_preserve_order(collected)
            except Exception:
                pass

    print("Pagination strategies exhausted. Returning collected canonical IDs (may be partial).")
    return dedupe_preserve_order(collected)

def main():
    if not TOKEN or TOKEN.startswith("eyJYOUR"):
        print("ERROR: open main_ideas.py and set TOKEN to your Bearer token string.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        # If your client requires 'app-id': 'app', uncomment:
        # "app-id": "app",
    }

    session = requests.Session()
    session.headers.update(headers)

    # base search payload (as in your example)
    base_payload = {
        "query": "*",
        "order": {"field": "createdDate", "direction": "DESC"},
        "where": [
            {"field": "type.keyword", "match": ["kickbox"], "matchMode": "EQUAL"},
            {"field": "createdDate", "match": [DATE_FROM, DATE_TO], "matchMode": "BETWEEN"},
        ],
        # "limit" will be set/managed by fetch_canonical_ids_smart
    }

    print("1) Fetching canonical IDs from ticket-attachment search (smart pagination)...")
    canonical_ids = fetch_canonical_ids_smart(session, base_payload)
    if not canonical_ids:
        print("No canonical IDs found. Exiting.")
        sys.exit(0)

    print(f"Total canonical IDs collected: {len(canonical_ids)} (SAFE_TOTAL_CAP={SAFE_TOTAL_CAP})")
    if len(canonical_ids) >= SAFE_TOTAL_CAP:
        print("WARNING: reached safe cap — there may be more records on the server.")

    # Prepare targets for fetchByCanonicalIdByBatch
    print(f"2) Fetching idea objects in batches of {BATCH_SIZE} ...")
    all_ideas: List[Dict] = []
    for idx, chunk in enumerate(chunked_iterable(canonical_ids, BATCH_SIZE), start=1):
        payload = {"context": "PASHAHolding", "targets": chunk}
        resp = try_post(session, FETCH_BY_CANONICAL_BATCH_URL, payload)
        if resp is None:
            print(f"Network error during batch {idx}. Aborting.")
            sys.exit(6)
        if resp.status_code == 401:
            print("Unauthorized (401) during batch fetch. Token invalid or expired.")
            sys.exit(7)
        if resp.status_code != 200:
            print(f"Batch endpoint returned {resp.status_code} for chunk {idx}: {resp.text[:300]}")
            sys.exit(8)
        try:
            data = resp.json()
        except Exception as e:
            print(f"Failed to parse JSON for chunk {idx}: {e}")
            sys.exit(9)

        # The endpoint example returns an object mapping internal ids to idea objects.
        if isinstance(data, dict):
            # extend with values (idea objects)
            ideas_list = [v for v in data.values() if isinstance(v, dict)]
        elif isinstance(data, list):
            ideas_list = [item for item in data if isinstance(item, dict)]
        else:
            print(f"Unexpected batch response format for chunk {idx}: {type(data)}")
            sys.exit(10)

        print(f"  chunk {idx}: fetched {len(ideas_list)} idea objects")
        all_ideas.extend(ideas_list)

    print(f"Total idea objects fetched: {len(all_ideas)}")
    if not all_ideas:
        print("No ideas returned. Exiting.")
        sys.exit(0)

    print("Normalizing and flattening idea objects...")
    df = normalize_ideas(all_ideas)

    print(f"Writing CSV -> {CSV_OUTPUT}")
    df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8")

    print(f"Writing Excel -> {XLSX_OUTPUT}")
    df.to_excel(XLSX_OUTPUT, index=False)

    print("Done.")
    print("Created files:")
    print(" -", CSV_OUTPUT)
    print(" -", XLSX_OUTPUT)

if __name__ == "__main__":
    main()
