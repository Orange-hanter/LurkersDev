#!/usr/bin/env python3
"""
Add YAML frontmatter tags to all .md files in RESTATE vault.
Rules based on directory location.
"""
import os
import re

VAULT = "/Users/dakh/Library/Mobile Documents/iCloud~md~obsidian/Documents/RESTATE"

def get_tags_for_path(rel_path):
    """Determine which tags to add based on file's directory location."""
    parts = rel_path.replace("\\", "/").split("/")
    
    # Templates
    if "_templates" in parts:
        return ["area/work", "type/template", "status/active"]
    
    # Inbox
    if "Inbox" in parts:
        return ["area/work", "type/note", "status/active"]
    
    # AWS / operations
    if "aws" in parts:
        return ["area/work", "type/runbook", "status/active"]
    
    # Domain specific
    if "Domain specific" in parts:
        return ["area/work", "type/doc", "status/active"]
    
    # Specification analysis (both variants)
    if "Specification analisys" in parts or "Specification analysis" in parts or "analysis" in parts:
        return ["area/work", "type/spec", "status/active"]
    
    # Customer specification
    if "Customer specification" in parts:
        if "Archive" in parts:
            return ["area/work", "type/spec", "status/archived"]
        return ["area/work", "type/spec", "status/active"]
    
    # Modules
    if "Modules" in parts:
        if "Archive" in parts:
            return ["area/work", "type/spec", "status/archived"]
        return ["area/work", "type/spec", "status/active"]
    
    # Root-level files - determine by content/convention
    filename = parts[-1] if parts else ""
    
    # Architecture files
    if filename in ("Architecture.md",):
        return ["area/work", "type/adr", "status/active"]
    
    # Core doc files
    if filename in ("Home.md", "NAVIGATION.md", "Documentation Graph.md",
                    "SYSTEM_OVERVIEW.md", "Technical Specification.md",
                    "Master Project Document.md", "User Stories.md",
                    "Open Questions.md", "Recommended flow.md",
                    "DDL Schema.md", "Logging.md", "Schema Evolution Plan.md",
                    "Specification analisys.md",
                    "Sensitive Data Protection Standard.md",
                    "Delivery plan (draft).md"):
        return ["area/work", "type/doc", "status/active"]
    
    # Untitled / misc
    if filename in ("Untitled.md",):
        return ["area/work", "type/note", "status/active"]
    
    # Default
    return ["area/work", "type/doc", "status/active"]


def has_frontmatter(content):
    """Check if content starts with YAML frontmatter (--- ... ---)."""
    return content.startswith("---")


def parse_frontmatter(content):
    """Extract the frontmatter block and the rest of the content."""
    if not content.startswith("---"):
        return None, content
    
    # Find the closing ---
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if match:
        return match.group(1), content[match.end():]
    
    # Try with no trailing newline
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if match:
        return match.group(1), content[match.end():]
    
    return None, content


def parse_tags_from_yaml(yaml_block):
    """Extract tags list from YAML frontmatter block."""
    # Match tags: [item1, item2, ...]
    match = re.search(r'^tags:\s*\[(.*?)\]', yaml_block, re.MULTILINE)
    if match:
        raw = match.group(1)
        tags = [t.strip() for t in raw.split(",")]
        return tags
    return None


def tag_exists(tag, tags_list):
    """Check if a tag (e.g. 'area/work') exists in tags list (e.g. ['area/work', 'type/doc'])."""
    return tag in tags_list


def add_tags_to_frontmatter(yaml_block, new_tags):
    """Add missing tags to the YAML frontmatter block."""
    existing_tags = parse_tags_from_yaml(yaml_block)
    
    if existing_tags is not None:
        # Add only missing ones
        for tag in new_tags:
            if not tag_exists(tag, existing_tags):
                existing_tags.append(tag)
        
        # Replace the tags line
        tags_str = ", ".join(existing_tags)
        
        def replace_tags(m):
            return f"tags: [{tags_str}]"
        
        new_yaml = re.sub(r'^tags:\s*\[.*?\]', replace_tags, yaml_block, count=1, flags=re.MULTILINE)
        return new_yaml
    else:
        # No tags key exists - add it before the first property
        tags_str = ", ".join(new_tags)
        new_yaml = f"tags: [{tags_str}]\n" + yaml_block
        return new_yaml


def process_file(filepath):
    """Process a single markdown file."""
    rel_path = os.path.relpath(filepath, VAULT)
    new_tags = get_tags_for_path(rel_path)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if has_frontmatter(content):
        yaml_block, rest = parse_frontmatter(content)
        if yaml_block is not None:
            new_yaml = add_tags_to_frontmatter(yaml_block, new_tags)
            if new_yaml != yaml_block:
                new_content = f"---\n{new_yaml}\n---{rest}"
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return "UPDATED", rel_path
            else:
                return "NO_CHANGE", rel_path
        else:
            return "PARSE_ERR", rel_path
    else:
        # No frontmatter - create it
        tags_str = ", ".join(new_tags)
        new_content = f"---\ntags: [{tags_str}]\n---\n\n{content}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return "ADDED", rel_path


def main():
    stats = {"ADDED": 0, "UPDATED": 0, "NO_CHANGE": 0, "PARSE_ERR": 0, "ERROR": 0}
    
    for root, dirs, files in os.walk(VAULT):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                status, rel = process_file(fpath)
                stats[status] += 1
                if status != "NO_CHANGE":
                    print(f"[{status:10s}] {rel}")
            except Exception as e:
                stats["ERROR"] += 1
                rel = os.path.relpath(fpath, VAULT)
                print(f"[ERROR     ] {rel}: {e}")
    
    print("\n=== SUMMARY ===")
    print(f"  Frontmatter ADDED:    {stats['ADDED']}")
    print(f"  Frontmatter UPDATED:  {stats['UPDATED']}")
    print(f"  No change needed:     {stats['NO_CHANGE']}")
    print(f"  Parse errors:         {stats['PARSE_ERR']}")
    print(f"  Errors:               {stats['ERROR']}")
    print(f"  TOTAL processed:      {sum(stats.values())}")


if __name__ == "__main__":
    main()
