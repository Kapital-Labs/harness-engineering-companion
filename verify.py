"""Run chapter suites in separate processes to preserve checkpoint imports."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
for chapter in sorted(root.glob('ch[0-9][0-9]')):
    if not list(chapter.glob('test*.py')):
        continue
    python = str(chapter/'.venv/bin/python') if chapter.name == 'ch17' else sys.executable
    if chapter.name == 'ch17' and not Path(python).exists():
        raise SystemExit('Install Chapter 17 dependencies per ch17/README.md first.')
    print(f'Verifying {chapter.name}', flush=True)
    result = subprocess.run([python, '-m', 'unittest', 'discover'], cwd=chapter)
    if result.returncode:
        raise SystemExit(result.returncode)
print('All chapter suites passed.')
