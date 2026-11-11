import json
import unittest
from revision_full.sse_transport import ChatAccumulator, consume_lines


class SSETests(unittest.TestCase):
    def test_fragmented_parallel_tools_and_terminal_usage(self):
        a = ChatAccumulator()
        chunks = [
            {"id":"gen-test","provider":"Z.AI","choices":[{"index":0,"delta":{"reasoning":"think","tool_calls":[{"index":1,"id":"b","function":{"name":"bash","arguments":'{"command":"'}},{"index":0,"id":"a","function":{"name":"bash","arguments":'{"command":"'}}]},"finish_reason":None}]},
            {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":'one"}'}},{"index":1,"function":{"arguments":'two"}'}}]},"finish_reason":"tool_calls"}]},
            {"choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":"tool_calls"}],"usage":{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15,"cost":.01}},
        ]
        lines = [": OPENROUTER PROCESSING", ""]
        for c in chunks:
            lines += ["data: "+json.dumps(c), ""]
        lines += ["data: [DONE]", ""]
        consume_lines(lines, a)
        r = a.result()
        self.assertEqual(r["usage"]["total_tokens"],15)
        self.assertEqual([t["id"] for t in r["choices"][0]["message"]["tool_calls"]],["a","b"])
        self.assertEqual(r["choices"][0]["message"]["tool_calls"][1]["function"]["arguments"],'{"command":"two"}')
        self.assertEqual(r["choices"][0]["message"]["reasoning"],"think")

    def test_truncation_and_error_never_become_complete_answers(self):
        a=ChatAccumulator()
        a.add(json.dumps({"choices":[{"index":0,"delta":{"content":"Partial"},"finish_reason":None}]}))
        with self.assertRaises(AssertionError):a.result()
        with self.assertRaises(ValueError):a.add(json.dumps({"error":{"message":"Disconnected"}}))

    def test_text_chunks_and_multiline_sse(self):
        a=ChatAccumulator()
        consume_lines(['data: {"id":"test",','data: "choices":[{"index":0,"delta":{"content":"hello"},"finish_reason":null}]}',"",
                       'data: {"choices":[{"index":0,"delta":{"content":" world"},"finish_reason":"stop"}],"usage":{"total_tokens":3}}',"",
                       'data: [DONE]',""],a)
        self.assertEqual(a.result()["choices"][0]["message"]["content"],"hello world")

    def test_done_stops_before_broken_http_tail(self):
        a=ChatAccumulator()
        def lines():
            yield 'data: {"choices":[{"index":0,"delta":{"content":"ok"},"finish_reason":"stop"}],"usage":{"total_tokens":1}}'
            yield ''
            yield 'data: [DONE]'
            yield ''
            raise RuntimeError("HTTP tail after complete application response")
        consume_lines(lines(),a)
        self.assertEqual(a.result()["choices"][0]["message"]["content"],"ok")


if __name__=="__main__":unittest.main()
