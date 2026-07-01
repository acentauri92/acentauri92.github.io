#!/usr/bin/env python3
"""
add-photo.py — Add a photo to dheeraj-reddy.in/photography/

USAGE
  python3 add-photo.py                  Interactive mode (recommended)
  python3 add-photo.py --help           Show this help
  python3 add-photo.py --list           List all photos currently on the site

WHAT IT DOES
  1. Asks for the image file (any name, any device filename is fine)
  2. Asks for a caption — shown in the lightbox on the site
  3. Suggests a clean slug based on the caption (e.g. "rain-vortex-singapore")
     You can accept the suggestion or type your own
  4. Renames the image to <slug>.<ext> and copies it to assets/images/photos/
  5. Appends the entry to _data/photos.yml
  6. Optionally commits and pushes to GitHub (site rebuilds automatically)

SLUG RULES
  - Lowercase letters, numbers, and hyphens only
  - No spaces or special characters
  - Keep it short and descriptive: "golden-sunset-mauritius", "marina-bay-christmas"
  - If the slug is already taken, a number is appended automatically (-2, -3, ...)

SUPPORTED FORMATS
  .jpg  .jpeg  .png  .webp  .heic

EXAMPLES
  Run interactively:
    python3 add-photo.py

  List existing photos:
    python3 add-photo.py --list
"""

import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(REPO, "assets", "images", "photos")
PHOTOS_YML = os.path.join(REPO, "_data", "photos.yml")
SUPPORTED_EXT = (".jpg", ".jpeg", ".png", ".webp", ".heic")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def load_photos():
    photos = []
    if not os.path.exists(PHOTOS_YML):
        return photos
    with open(PHOTOS_YML) as f:
        current = {}
        for line in f:
            m_file = re.match(r"\s*-\s*file:\s*[\"']?(.+?)[\"']?\s*$", line)
            m_desc = re.match(r"\s+description:\s*[\"'](.+?)[\"']\s*$", line)
            if m_file:
                current = {"file": m_file.group(1).strip()}
            elif m_desc and current:
                current["description"] = m_desc.group(1).strip()
                photos.append(current)
                current = {}
    return photos


def existing_slugs():
    return {os.path.splitext(p["file"])[0] for p in load_photos()}


def prompt(label, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{label}{suffix}: ").strip()
    return val if val else default


def run(cmd):
    result = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n  Git error: {result.stderr.strip()}")
        sys.exit(1)


def cmd_list():
    photos = load_photos()
    if not photos:
        print("No photos found.")
        return
    print(f"\n{'#':<4}  {'Filename':<45}  Caption")
    print("-" * 90)
    for i, p in enumerate(photos, 1):
        slug = os.path.splitext(p["file"])[0]
        desc = p.get("description", "")
        print(f"{i:<4}  {p['file']:<45}  {desc}")
    print(f"\n{len(photos)} photo(s) total.\n")


def cmd_add():
    print("\n=== Add Photo to Photography Page ===")
    print("Type 'q' at any prompt to cancel.\n")

    # 1. Image path
    src = prompt("Image file path (drag & drop works too)")
    if src.lower() == "q":
        print("Cancelled.")
        sys.exit(0)
    src = src.strip("'\"").strip()
    src = os.path.expanduser(src)

    if not os.path.isfile(src):
        print(f"\n  Error: File not found: {src}")
        sys.exit(1)

    ext = os.path.splitext(src)[1].lower()
    if ext not in SUPPORTED_EXT:
        print(f"\n  Error: Unsupported format '{ext}'. Supported: {', '.join(SUPPORTED_EXT)}")
        sys.exit(1)

    size_mb = os.path.getsize(src) / (1024 * 1024)
    print(f"  Found: {os.path.basename(src)} ({size_mb:.1f} MB)")

    # 2. Description
    print()
    description = prompt("Caption (shown under the photo in the lightbox)")
    if not description or description.lower() == "q":
        print("Cancelled." if description.lower() == "q" else "  Error: Caption is required.")
        sys.exit(0 if description and description.lower() == "q" else 1)

    # 3. Slug
    suggested = slugify(description)[:50].rstrip("-")
    print()
    slug = prompt("Slug (filename, letters/numbers/hyphens only)", default=suggested)
    if slug.lower() == "q":
        print("Cancelled.")
        sys.exit(0)
    slug = slugify(slug)
    if not slug:
        print("  Error: Slug cannot be empty.")
        sys.exit(1)

    taken = existing_slugs()
    original = slug
    counter = 2
    while slug in taken:
        slug = f"{original}-{counter}"
        counter += 1
    if slug != original:
        print(f"  Note: '{original}' already exists — using '{slug}' instead.")

    dest_filename = f"{slug}{ext}"
    dest_path = os.path.join(PHOTOS_DIR, dest_filename)

    # 4. Confirm
    print(f"\n  {'File':<12}: {dest_filename}")
    print(f"  {'Caption':<12}: {description}")
    print(f"  {'Size':<12}: {size_mb:.1f} MB")
    print()
    confirm = input("Add this photo? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("Aborted.")
        sys.exit(0)

    # 5. Copy image
    shutil.copy2(src, dest_path)
    print(f"\n  Copied  → {dest_path}")

    # 6. Append to photos.yml
    entry = f'- file: "{dest_filename}"\n  description: "{description}"\n'
    with open(PHOTOS_YML, "a") as f:
        f.write(entry)
    print(f"  Updated → _data/photos.yml")

    # 7. Git commit and push
    print()
    push = input("Commit and push to GitHub? [Y/n]: ").strip().lower()
    if push != "n":
        run(["git", "add", dest_path, PHOTOS_YML])
        run(["git", "commit", "-m", f"Add photo: {slug}"])
        run(["git", "push"])
        print("  Pushed  → GitHub (site will rebuild in ~1 minute)")

    print("\nDone!\n")


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    if "--list" in args or "-l" in args:
        cmd_list()
        sys.exit(0)

    if args:
        print(f"Unknown argument: {args[0]}")
        print("Run with --help for usage.")
        sys.exit(1)

    cmd_add()


if __name__ == "__main__":
    main()
