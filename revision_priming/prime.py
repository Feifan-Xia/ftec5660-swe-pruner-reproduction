"""Require one initial hint decision, then preserve the original optional schema."""
import copy
import json

import httpx


def prime_body(body):
    updated = copy.deepcopy(body)
    tool = next((t for t in updated.get("tools", []) if t.get("function", {}).get("name") == "pruner_bash"), None)
    if tool is None:
        return None
    parameters = tool["function"]["parameters"]
    if "context_focus_question" not in parameters["required"]:
        parameters["required"].append("context_focus_question")
    parameters["properties"]["context_focus_question"]["minLength"] = 1
    return updated


def install():
    original = httpx.Client.send
    used = False

    def send(self, request, **kwargs):
        nonlocal used
        if not used and request.url.host in ["127.0.0.1", "localhost"] and request.url.port == 8879 and request.method == "POST":
            body = json.loads(request.content)
            updated = prime_body(body)
            if updated is not None:
                # The process owns one agent task. Preserve request options and all
                # messages; only the first native request's hint schema changes.
                used = True
                headers = dict(request.headers); headers.pop("content-length", None)
                request = httpx.Request(request.method, request.url, content=json.dumps(updated).encode(), headers=headers, extensions=request.extensions)
        return original(self, request, **kwargs)

    httpx.Client.send = send

