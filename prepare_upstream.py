"""Apply reproducible operational fixes to the pinned authors' runner."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'upstream/downstream_eval/multi_turn/sweqa'


def main():
    runner = SOURCE / 'openhands-qa/main.py'
    text = runner.read_text(encoding='utf-8')
    text = text.replace('print(LLM_CONFIG)', 'print("LLM configuration loaded (credentials hidden)")')
    text = text.replace('MAX_WORKERS = 16', 'MAX_WORKERS = 1')
    text = text.replace('_http_hack_enabled = setup_http_hack_for_claude()',
                        '_http_hack_enabled = False  # OpenAI-compatible route uses native httpx')
    text = text.replace('                    if hasattr(metrics, "token_usages") and metrics.token_usages:',
                        '                    elif hasattr(metrics, "token_usages") and metrics.token_usages:')
    text = text.replace('elif experiment == "pruner":\n', 'elif experiment in ("pruner", "recovery"):\n')
    recovery = '''if experiment == "recovery":
    from recovery_tool import make_recoverable, make_expand
    register_tool("Bash", make_recoverable)
    register_tool("ExpandObservation", make_expand)

'''
    if recovery not in text:
        text = text.replace('tools = [Tool(name="Bash")]', recovery + 'tools = [Tool(name="Bash")]\nif experiment == "recovery":\n    tools.append(Tool(name="ExpandObservation"))')
    marker = '# Load base paths from environment'
    addition = '''# Reproduction: identify this coding client and preserve a stable session.
LLM_CONFIG["extra_headers"] = {
    "User-Agent": "ftec5660-sweqa-reproduction/0.1",
    "x-opencode-session": os.environ.get("REPRO_SESSION_ID", "ftec5660-pilot"),
}

'''
    if addition not in text:
        text = text.replace(marker, addition + marker)
    runner.write_text(text, encoding='utf-8')
    model = ROOT / 'upstream/swe-pruner/src/swe_pruner/model_structure.py'
    code = model.read_text(encoding='utf-8')
    code = code.replace('attn_implementation: Optional[str] = "flash_attention_2"',
                        'attn_implementation: Optional[str] = "sdpa"')
    model.write_text(code, encoding='utf-8')
    tool = SOURCE / 'openhands-qa/tool_utils.py'
    code = tool.read_text(encoding='utf-8').replace('httpx.Client(timeout=60.0, proxy=None)',
                                                'httpx.Client(timeout=60.0, proxy=None, trust_env=False)')
    tool.write_text(code, encoding='utf-8')
    print('Prepared official runner: credential-safe logs, serial execution, provider headers.')


if __name__ == '__main__':
    main()
