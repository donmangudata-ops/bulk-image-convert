"""Cloud mode: run the hosted Apify Actor. Needs your own APIFY_TOKEN."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

ACTOR_ID = "conserving_celerytop/image-converter-compressor"
STORE_URL = "https://apify.com/conserving_celerytop/image-converter-compressor"
TOKEN_HELP = (
    "Cloud mode needs an Apify API token. Create a free account, copy your token from "
    "https://console.apify.com/settings/integrations and run:\n"
    "  export APIFY_TOKEN=your_token\n"
    f"Details and pricing: {STORE_URL}"
)


def build_run_input(urls: List[str], fmt: str, quality: int, max_width: Optional[int],
                    max_height: Optional[int], lossless: bool, keep_metadata: bool) -> dict:
    data = {
        "imageUrls": urls,
        "outputFormat": fmt,
        "quality": quality,
        "lossless": lossless,
        "keepMetadata": keep_metadata,
    }
    if max_width:
        data["maxWidth"] = max_width
    if max_height:
        data["maxHeight"] = max_height
    return data


def run_cloud(urls: List[str], out_dir: Path, **opts) -> int:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print(TOKEN_HELP, file=sys.stderr)
        return 2
    try:
        from apify_client import ApifyClient
    except ImportError:
        print("Install the cloud extra first: pip install 'bulk-image-convert[cloud]'", file=sys.stderr)
        return 2
    import urllib.request

    client = ApifyClient(token)
    print(f"Starting cloud run for {len(urls)} URL(s)...")
    run = client.actor(ACTOR_ID).call(run_input=build_run_input(urls, **opts))
    if not run:
        print("The cloud run did not return a result.", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = fail = 0
    for row in client.dataset(run["defaultDatasetId"]).iterate_items():
        if row.get("status") == "ok" and row.get("outputUrl"):
            name = row.get("outputKey") or f"image-{row.get('inputIndex')}.{row.get('outputFormat')}"
            urllib.request.urlretrieve(row["outputUrl"], out_dir / name)
            saved += row.get("savedBytes") or 0
            print(f"ok    {name}  {row.get('savedPercent')}% smaller")
        else:
            fail += 1
            print(f"fail  {row.get('imageUrl')}  {row.get('status')}", file=sys.stderr)
    print(f"Done. Saved {saved:,} bytes. {fail} failed. Files in {out_dir}")
    return 0 if not fail else 1
