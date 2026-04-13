from pathlib import Path
from datetime import datetime

NOTES_DIR = Path.home() / "JarvisNotes"
NOTES_DIR.mkdir(exist_ok=True)

def create_note(title: str, content: str) -> str:
    filename = NOTES_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title[:30]}.md"
    filename.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
    return str(filename)

def list_notes() -> list:
    return [f.name for f in sorted(NOTES_DIR.glob("*.md"), reverse=True)[:20]]

def read_note(filename: str) -> str:
    if not filename:
        return "No note specified."
    
    path = NOTES_DIR / filename
    
    if path.exists():
        return path.read_text(encoding="utf-8")
    else:
        return f"Note not found: {filename}"