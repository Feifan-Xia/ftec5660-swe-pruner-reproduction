"""Apply reproducible operational fixes to the pinned authors' runner."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'upstream/downstream_eval/multi_turn/sweqa'


def main():
    runner = SOURCE / 'openhands-qa/main.py'
    text = runner.read_text(encoding='utf-8')
    text = text.replace('print(LLM_CONFIG)', 'print("LLM configuration loaded (credentials hidden)")')
    text = text.replace('MAX_WORKERS = 16', 'MAX_WORKERS = 1')
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
    print('Prepared official runner: credential-safe logs, serial execution, provider headers.')


if __name__ == '__main__':
    main()
