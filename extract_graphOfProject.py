import os
import argparse
from pathlib import Path

def build_tree(root_path: Path, prefix: str = "", ignore_dirs=None, ignore_files=None):
    """
    Recursively build a tree string representation of the directory structure.
    """
    if ignore_dirs is None:
        ignore_dirs = {
            '__pycache__', '.git', '.venv', 'venv', '.idea', 'node_modules',
            'build', 'dist', '.pytest_cache', '.mypy_cache'
        }
    if ignore_files is None:
        ignore_files = {'.gitignore', '.env', '.DS_Store'}

    tree_lines = []
    contents = sorted(root_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

    for index, item in enumerate(contents):
        if item.name in ignore_dirs or item.name.startswith('.'):
            continue
        if item.is_file() and item.name in ignore_files:
            continue

        connector = "├── " if index < len(contents) - 1 else "└── "
        tree_lines.append(prefix + connector + item.name)

        if item.is_dir():
            extension = "│   " if index < len(contents) - 1 else "    "
            tree_lines.extend(build_tree(item, prefix + extension, ignore_dirs, ignore_files))

    return tree_lines

def main():
    parser = argparse.ArgumentParser(description="Generate a tree view of your Flask/Python project structure.")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the project root directory (default: current directory)"
    )
    args = parser.parse_args()

    project_root = Path(args.path).resolve()

    if not project_root.is_dir():
        print(f"Error: '{project_root}' is not a valid directory.")
        return

    print(f"{project_root.name}/")
    tree = build_tree(project_root)
    for line in tree:
        print(line)

    # Optional: also print total counts
    py_files = len(list(project_root.rglob("*.py")))
    print(f"\n{py_files} Python files found.")

if __name__ == "__main__":
    main()