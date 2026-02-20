import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

PROMPTS = {

    "parser": "parser.txt",
    "dates": "dates.txt",
    "congratulations": "congratulations.txt",
    "reponse": "response.txt"

}

def find_project_root(start: Optional[Path] = None) -> Path:

    if start is None:
        start = Path(__file__).resolve()

    markers = [
        "prompts",
        "calendar",
        "email",
    ]

    current = start if start.is_dir() else start.parent

    while True:
        if all((current / marker).exists() and (current / marker).is_dir() for marker in markers):
            return current

        if current == current.parent:
            break

        current = current.parent

    return Path(os.getcwd()).resolve()

def load_prompts(state: Dict[str, Any]) -> Dict[str, Any]:

    if not isinstance(state, dict):
        state = {}

    root = find_project_root()
    prompt_dir = root / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_dict: Dict[str, str] = {}

    for prompt, file_path in PROMPTS.items():
        path = prompt_dir / file_path
        if path.exists() and path.is_file():
            try:
                prompt_text = path.read_text(encoding="utf-8")
                prompt_text = prompt_text.strip() if isinstance(prompt_text, str) else ""
                if prompt_text:
                    prompt_dict[prompt] = prompt_text
            except:
                pass

    return {"root": str(root), "prompts": prompt_dict}
