"""Regression tests for USE authority-boundary resilience."""
import unittest
from unittest.mock import patch
from boundary_resilience import FRESH, STALE, UNAVAILABLE, StaleAuthorityCache, preserve_specialist_payload

class BoundaryResilienceTests(unittest.TestCase):
    def test_fresh_snapshot_is_reused_within_ttl(self):
        cache=StaleAuthorityCache(fresh_ttl_seconds=60); calls={"n":0}
        def loader(): calls["n"]+=1; return [{"node_id":"atlas"}]
        first,s1=cache.get(loader); second,s2=cache.get(loader)
        self.assertEqual((s1,s2,calls["n"],first),(FRESH,FRESH,1,second))

    def test_failure_uses_bounded_stale_snapshot(self):
        cache=StaleAuthorityCache(fresh_ttl_seconds=0,max_stale_seconds=60,failure_retry_seconds=30)
        with patch("boundary_resilience.time.time",side_effect=[100.0,101.0]):
            value,state=cache.get(lambda:[{"node_id":"glossary"}])
            stale,stale_state=cache.get(lambda:(_ for _ in ()).throw(RuntimeError("authority unavailable")))
        self.assertEqual((state,stale_state,value,stale),(FRESH,STALE,value,value))
        self.assertEqual(cache.snapshot()["failure_count"],1)

    def test_stale_snapshot_expires_fail_closed(self):
        cache=StaleAuthorityCache(fresh_ttl_seconds=0,max_stale_seconds=10,failure_retry_seconds=30)
        with patch("boundary_resilience.time.time",side_effect=[100.0,111.0,112.0]):
            cache.get(lambda:[{"node_id":"glyph"}])
            value,state=cache.get(lambda:(_ for _ in ()).throw(RuntimeError("authority unavailable")))
            value2,state2=cache.get(lambda:(_ for _ in ()).throw(RuntimeError("authority unavailable")))
        self.assertEqual((value,state,value2,state2),([],UNAVAILABLE,[],UNAVAILABLE))

    def test_specialist_payload_is_preserved_without_mutation(self):
        payload={"title":"Guardian Glyph Archives","resources":[{"url":"https://example.test/glyph"}]}
        preserved=preserve_specialist_payload(payload,required_keys=("title","resources"))
        preserved["resources"][0]["url"]="changed"
        self.assertEqual(payload["resources"][0]["url"],"https://example.test/glyph")

    def test_missing_specialist_contract_fails_closed(self):
        with self.assertRaises(ValueError):
            preserve_specialist_payload({"title":"Atlas"},required_keys=("resources",))

if __name__=="__main__":
    unittest.main()
