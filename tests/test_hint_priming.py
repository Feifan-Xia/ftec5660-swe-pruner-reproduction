import copy
import json
import unittest
from unittest.mock import patch

import httpx
from revision_priming.prime import install, prime_body


class HintPrimingTests(unittest.TestCase):
    def fixture(self):
        return {"model": "z-ai/glm-4.6", "messages": [{"role": "user", "content": "Question"}], "temperature": 0,
                "tools": [{"type": "function", "function": {"name": "pruner_bash", "description": "Original description",
                           "parameters": {"required": ["command"], "properties": {"command": {"type": "string"}, "context_focus_question": {"type": "string"}}}}}]}

    def test_only_first_native_request_changes_and_original_remains_intact(self):
        body = self.fixture(); old = copy.deepcopy(body); captured = []
        def capture(request):
            captured.append(json.loads(request.content))
            self.assertEqual(int(request.headers["content-length"]), len(request.content))
            self.assertEqual(request.headers["x-opencode-session"], "test")
            return httpx.Response(200, json={"ok": True})
        original = httpx.Client.send
        try:
            install()
            with httpx.Client(transport=httpx.MockTransport(capture)) as client:
                judge = {"model": "openai/gpt-5", "messages": []}
                for payload in [judge, body, body]:
                    client.post("http://127.0.0.1:8879/v1/chat/completions", json=payload, headers={"x-opencode-session": "test"})
            self.assertEqual(body, old)
            self.assertEqual(captured[0], judge)
            self.assertEqual(captured[1], prime_body(body))
            self.assertEqual(captured[2], body)
            restored = copy.deepcopy(captured[1])
            p = restored["tools"][0]["function"]["parameters"]
            p["required"].remove("context_focus_question")
            del p["properties"]["context_focus_question"]["minLength"]
            self.assertEqual(restored, body)
        finally:
            httpx.Client.send = original


if __name__ == "__main__":
    unittest.main()
