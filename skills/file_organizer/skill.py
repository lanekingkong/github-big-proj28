"""
Example Skill: File Organizer

Automatically organizes files by type into categorized folders.
Uses UniSkill's lifecycle management and security scanning.
"""

from pathlib import Path
from typing import Optional


FILE_CATEGORIES = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".go", ".rs"],
    "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
    "Presentations": [".ppt", ".pptx", ".odp"],
}


def get_category(file_path: Path) -> str:
    """Determine the category of a file based on extension."""
    suffix = file_path.suffix.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if suffix in extensions:
            return category
    return "Other"


def organize_directory(directory: str, recursive: bool = False) -> dict:
    """Organize files in a directory into categorized folders.

    Args:
        directory: Path to the directory to organize
        recursive: Whether to process subdirectories

    Returns:
        Summary of organization results
    """
    target = Path(directory)
    if not target.exists():
        return {"status": "error", "message": f"Directory not found: {directory}"}

    stats = {"moved": 0, "skipped": 0, "errors": 0, "details": []}

    # Create category folders
    for category in FILE_CATEGORIES:
        (target / category).mkdir(exist_ok=True)
    (target / "Other").mkdir(exist_ok=True)

    # Organize files
    pattern = "**/*" if recursive else "*"
    for file_path in target.glob(pattern):
        if not file_path.is_file():
            continue
        if file_path.parent != target and not recursive:
            continue

        category = get_category(file_path)
        dest_dir = target / category

        if file_path.parent == dest_dir:
            stats["skipped"] += 1
            continue

        try:
            file_path.rename(dest_dir / file_path.name)
            stats["moved"] += 1
            stats["details"].append(f"{file_path.name} -> {category}/")
        except Exception as e:
            stats["errors"] += 1
            stats["details"].append(f"Error moving {file_path.name}: {e}")

    return stats


def execute(input_data: dict) -> dict:
    """UniSkill entry point."""
    directory = input_data.get("directory", ".")
    recursive = input_data.get("recursive", False)
    return organize_directory(directory, recursive)
