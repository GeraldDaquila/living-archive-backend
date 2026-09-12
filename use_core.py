RUNTIME_PROCESS_ID = os.getpid()

# Optional-but-hard production provenance gate. The expected raw source hash
# is supplied out-of-band (Render environment variable) so the expected value
# cannot alter the source bytes whose hash it is checking. This avoids the
# impossible self-referential construction of embedding a raw file hash inside
# the same file. Local development may leave it unset; LIVE deployment must
# provide it.
EXPECTED_RUNTIME_SOURCE_SHA256 = os.getenv(
    "USE_EXPECTED_SOURCE_SHA256", ""
).strip().lower()
if EXPECTED_RUNTIME_SOURCE_SHA256:
    if RUNTIME_SOURCE_SHA256 != EXPECTED_RUNTIME_SOURCE_SHA256:
        print(
            "USE SOURCE PROVENANCE FAILURE: "
            f"expected_source_sha256={EXPECTED_RUNTIME_SOURCE_SHA256}, "
            f"actual_source_sha256={RUNTIME_SOURCE_SHA256}, "
            f"file={os.path.abspath(__file__)}"
        )
        raise RuntimeError(
            "USE source provenance mismatch; refusing to serve requests."
        )
    print(
        "USE SOURCE PROVENANCE: valid=True, "
        f"source_sha256={RUNTIME_SOURCE_SHA256}"
    )
else:
    print(
        "USE SOURCE PROVENANCE: expected SHA not configured; "
        f"source_sha256={RUNTIME_SOURCE_SHA256}. "
        "LIVE Render deployment must provide USE_EXPECTED_SOURCE_SHA256."
    )
