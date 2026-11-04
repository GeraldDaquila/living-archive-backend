"""Regression tests for the strict browser-origin boundary."""
import asyncio
import unittest
import main

class CorsBoundaryTests(unittest.TestCase):
    def run_app(self, origin, method="GET", preflight=False):
        sent=[]
        async def inner(scope, receive, send):
            await send({"type":"http.response.start","status":200,"headers":[(b"access-control-allow-origin",b"*"),(b"x-test",b"ok")]})
            await send({"type":"http.response.body","body":b"ok"})
        scope={"type":"http","method":method,"headers":[(b"origin",origin.encode())] + ([(b"access-control-request-method",b"GET")] if preflight else [])}
        async def receive(): return {"type":"http.request","body":b"","more_body":False}
        async def send(message): sent.append(message)
        asyncio.run(main._StrictCorsBoundary(inner)(scope,receive,send))
        return sent

    def headers(self, sent):
        return dict(sent[0].get("headers",[]))

    def test_untrusted_origin_does_not_receive_cors_header(self):
        headers=self.headers(self.run_app("https://untrusted.example"))
        self.assertNotIn(b"access-control-allow-origin",headers)

    def test_canonical_origin_receives_exact_origin(self):
        headers=self.headers(self.run_app("https://geralddaquila.com"))
        self.assertEqual(headers.get(b"access-control-allow-origin"),b"https://geralddaquila.com")

    def test_untrusted_preflight_has_no_cors_grant(self):
        headers=self.headers(self.run_app("https://untrusted.example","OPTIONS",True))
        self.assertNotIn(b"access-control-allow-origin",headers)

if __name__=="__main__":
    unittest.main()
