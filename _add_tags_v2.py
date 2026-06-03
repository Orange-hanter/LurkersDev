#!/usr/bin/env python3
"""
Add YAML frontmatter tags to all .md files in RESTATE vault.
Rules based on directory location.
"""
import os
import re
import sys

VAULT = "/Users/dakh/Library/Mobile Documents/iCloud~md~obsidian/Documents/RESTATE"

def get_tags_for_path(rel_path):
    """Determine which tags to add based on file's directory location."""
    parts = rel_path.replace("\\", "/").split("/")
    
    if "_templates" in parts:
        return ["area/work", "type/template", "status/active"]
    if "Inbox" in parts:
        return ["area/work", "type/note", "status/active"]
    if "aws" in parts:
        return ["area/work", "type/runbook", "status/active"]
    if "Domain specific" in parts:
        return ["area/work", "type/doc", "status/active"]
    if "Specification analisys" in parts or "Specification analysis" in parts or "analysis" in parts:
        return ["area/work", "type/spec", "status/active"]
    if "Customer specification" in parts:
        if "Archive" in parts:
            return ["area/work", "type/spec", "status/archived"]
        return ["area/work", "type/spec", "status/active"]
    if "Modules" in parts:
        if "Archive" in parts:
            return ["area/work", "type/spec", "status/archived"]
        return ["area/work", "type/spec", "status/active"]
    
    filename = parts[-1] if parts else ""
    if filename in ("Home.md", "NAVIGATION.md", "Documentation Graph.md",
                    "SYSTEM_OVERVIEW.md", "Technical Specification.md",
                    "Master Project Document.md", "User Stories.md",
                    "Open Questions.md", "Recommended flow.md",
                    "DDL Schema.md", "Logging.md", "Schema Evolution Plan.md",
                    "Specification analisys.md",
                    "Sensitive Data Protection Standard.md",
                    "Delivery plan (draft).md"):
        return ["area/work", "type/doc", "status/active"]
    return ["area/work", "type/doc", "status/active"]


def process_file(filepath):
    """Process a single markdown file."""
    rel_path = os.path.relpath(filepath, VAULT)
    new_tags = get_tags_for_path(rel_path)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file has frontmatter (starts with ---)
    if content.startswith("---"):
        # Find closing ---
        idx = content.find("---", 3)
        if idx != -1:
            front = content[3:idx].strip()
            rest = content[idx+3:]
            
            # Check for tags in frontmatter
            tag_match = re.search(r'^tags:\s*\[(.*?)\]', front, re.MULTILINE)
            if tag_match:
                existing = [t.strip() for t in tag_match.group(1).split(",")]
                missing = [t for t in new_tags if t not in existing]
                if missing:
                    new_tags_list = ", ".join(existing + missing)
                    new_front = re.sub(r'^tags:\s*\[.*?\]', f'tags: [{new_tags_list}]', front, count=1, flags=re.MULTILINE)
                    new_content = f"---\n{new_front}\n---{rest}"
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    return "UPDATED", rel_path
                else:
                    return "NO_CHANGE", rel_path
            else:
                # No tags line in frontmatter - add it
                tags_str = ", ".join(new_tags)
                new_front = f"tags: [{tags_str}]\n" + front
                new_content = f"---\n{new_front}\n---{rest}"
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return "ADDED_TAGS", rel_path
        return "PARSE_ERR", rel_path
    else:
        # No frontmatter - create it
        tags_str = ", ".join(new_tags)
        new_content = f"---\ntags: [{tags_str}]\n---\n\n{content}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return "ADDED", rel_path


def main():
    stats = {"ADDED": 0, "ADDED_TAGS": 0, "UPDATED": 0, "NO_CHANGE": 0, "PARSE_ERR": 0, "ERROR": 0}
    
    for root, dirs, files in os.walk(VAULT):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                status, rel = process_file(fpath)
                stats[status] += 1
                if status != "NO_CHANGE":
                    print(f"[{status:12s}] {rel}")
            except Exception as e:
                stats["ERROR"] += 1
                rel = os.path.relpath(fpath, VAULT)
                print(f"[ERROR       ] {rel}: {e}")
    
    print("\n=== SUMMARY ===")
    for k, v in stats.items():
        print(f"  {k:12s}: {v}")
    print(f"  TOTAL       : {sum(stats.values())}")
    
    # Exit with error if any failures
    if stats["ERROR"] > 0 or stats["PARSE_ERR"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
