"""Receive upstream SSE heartbeats, preserve evidence, return complete chat JSON."""
import copy
import hashlib
import json
import time
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


class ChatAccumulator:
    def __init__(self):
        self.meta = {}
        self.choices = {}
        self.usage = None
        self.done = False

    def add(self, value):
        if value == "[DONE]":
            self.done = True
            return
        item = json.loads(value)
        if item.get("error"):
            raise ValueError("Upstream SSE reports an error: " + str(item["error"]))
        for key in ["id", "created", "model", "provider", "system_fingerprint", "service_tier"]:
            if key in item:
                self.meta[key] = item[key]
        if item.get("usage"):
            self.usage = item["usage"]
        for c in item.get("choices", []):
            i = c["index"]
            row = self.choices.setdefault(i, {"index": i, "finish_reason": None, "message": {"role": "assistant", "content": None}, "_tools": {}})
            for key in ["finish_reason", "native_finish_reason", "logprobs"]:
                if c.get(key) is not None:
                    row[key] = c[key]
            delta = c.get("delta", {})
            for key in ["content", "reasoning", "reasoning_content", "refusal"]:
                if delta.get(key) is not None:
                    row["message"][key] = (row["message"].get(key) or "") + delta[key]
            if delta.get("reasoning_details"):
                row["message"].setdefault("reasoning_details", []).extend(copy.deepcopy(delta["reasoning_details"]))
            for tool in delta.get("tool_calls", []):
                assembled = row["_tools"].setdefault(tool["index"], {"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                if tool.get("id"):
                    assembled["id"] = tool["id"]
                if tool.get("type"):
                    assembled["type"] = tool["type"]
                for key in ["name", "arguments"]:
                    if tool.get("function", {}).get(key):
                        assembled["function"][key] += tool["function"][key]

    def result(self):
        assert self.done and self.usage and self.choices, "Incomplete SSE; retain failure evidence"
        rows = []
        for i, value in sorted(self.choices.items()):
            row = copy.deepcopy(value)
            assert row["finish_reason"] and row["finish_reason"] != "error"
            tools = row.pop("_tools")
            if tools:
                row["message"]["tool_calls"] = [v for _, v in sorted(tools.items())]
                for tool in row["message"]["tool_calls"]:
                    assert tool["id"] and tool["function"]["name"]
                    json.loads(tool["function"]["arguments"])
            # GLM's ordinary JSON response exposes one reasoning string. Its SSE
            # details repeat that same text as fragments; keep the full originals
            # in raw_sse.txt and match the established downstream message shape.
            if str(self.meta.get("model", "")).startswith("z-ai/glm-4.6") and "reasoning" in row["message"]:
                row["message"].pop("reasoning_details", None)
            rows.append(row)
        return {**self.meta, "object": "chat.completion", "choices": rows, "usage": self.usage}


def consume_lines(lines, accumulator):
    data = []
    for line in lines:
        if line == "":
            if data:
                accumulator.add("\n".join(data))
                data = []
                if accumulator.done:
                    return
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
        # SSE comments, event IDs and keepalive fields are transport metadata.
    if data:
        accumulator.add("\n".join(data))


def install():
    original = httpx.Client.post

    def post(self, url, *args, **kwargs):
        body = kwargs.get("json")
        if str(url) != "https://openrouter.ai/api/v1/chat/completions" or not isinstance(body, dict) or body.get("stream"):
            return original(self, url, *args, **kwargs)
        assert not args
        folder = ROOT / "runs/full/stream_transport" / uuid.uuid4().hex
        folder.mkdir(parents=True, exist_ok=True)
        upstream = copy.deepcopy(body)
        upstream["stream"] = True
        upstream["stream_options"] = {"include_usage": True}
        options = dict(kwargs); options["json"] = upstream
        meta = {"started": time.time(), "original_body_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest(),
                "model": body.get("model"), "transport_change": "Only stream=true and include_usage; downstream receives complete JSON."}
        (folder / "upstream_request.json").write_text(json.dumps(upstream, ensure_ascii=False, indent=2), encoding="utf-8")
        acc = ChatAccumulator()
        try:
            with self.stream("POST", url, **options) as response:
                meta.update(status=response.status_code, generation_header=response.headers.get("x-generation-id"))
                (folder / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
                if response.status_code != 200:
                    content = response.read()
                    (folder / "http_error.txt").write_bytes(content)
                    return httpx.Response(response.status_code, content=content, headers={"content-type": response.headers.get("content-type", "application/json")}, request=response.request)
                with (folder / "raw_sse.txt").open("w", encoding="utf-8") as raw:
                    def recording_lines():
                        for line in response.iter_lines():
                            raw.write(line + "\n"); raw.flush()
                            yield line
                    consume_lines(recording_lines(), acc)
                result = acc.result()
                (folder / "assembled.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                meta.update(ended=time.time(), generation_id=result.get("id"), complete=True)
                return httpx.Response(200, json=result, request=response.request)
        except Exception as exc:
            meta.update(ended=time.time(), complete=False, error=type(exc).__name__, detail=str(exc), partial_generation_id=acc.meta.get("id"))
            raise
        finally:
            (folder / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    httpx.Client.post = post
