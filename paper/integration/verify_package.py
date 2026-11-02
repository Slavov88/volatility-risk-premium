"""Verify immutable package bytes and losslessly compressed scientific records."""

from pathlib import Path
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    manifest = json.loads((HERE / "package-manifest.json").read_bytes())
    for name, record in manifest["files"].items():
        path = HERE / name
        raw = path.read_bytes()
        if sha(raw) != record["sha256"] or len(raw) != record["bytes"]:
            raise ValueError("Package file differs: " + name)
    directory = HERE / "audits/econometrics"
    compressed = json.loads((directory / "compressed-artifacts.json").read_bytes())
    for name, record in compressed.items():
        raw = gzip.decompress((directory / name).read_bytes())
        if (
            sha(raw) != record["uncompressed_sha256"]
            or len(raw) != record["uncompressed_bytes"]
        ):
            raise ValueError("Logical scientific record differs: " + name)
        json.loads(raw)
    print(
        f"Verified {len(manifest['files'])} package files and {len(compressed)} lossless scientific records"
    )


if __name__ == "__main__":
    main()
