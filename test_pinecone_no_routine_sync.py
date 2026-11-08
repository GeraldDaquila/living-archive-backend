import archive_crosslink


class _ExplosiveIndex:
    def __getattr__(self, name):
        raise AssertionError(f"runtime Pinecone access attempted: {name}")


def test_runtime_refresh_is_hard_disabled_even_when_forced():
    assert archive_crosslink.start_refresh(_ExplosiveIndex(), object(), force=True) is False


def test_runtime_policy_is_not_environment_opt_in():
    source = open(archive_crosslink.__file__, encoding="utf-8").read()
    start = source.index("def start_refresh")
    end = source.index("def _refresh_worker", start)
    runtime_entrypoint = source[start:end]
    assert "ALLOW_LEGACY_PINECONE_CROSSLINK_REFRESH" not in runtime_entrypoint
    assert "canonical_shared_index_no_monthly_sync" in runtime_entrypoint
