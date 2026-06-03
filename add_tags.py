#!/usr/bin/env python3
"""Add YAML frontmatter tags to Obsidian .md files in Archive, Education, and fation-ai vaults."""

import os
import re
import yaml
from pathlib import Path
import datetime

VAULT = Path("/Users/dakh/Library/Mobile Documents/iCloud~md~obsidian/Documents")
REPORT = Path("/Users/dakh/Git/_my/LurkersDev/tags_report.txt")

def parse_frontmatter(content):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if m:
        try:
            fm = yaml.safe_load(m.group(1))
            rest = content[m.end():]
            return (fm if isinstance(fm, dict) else {}), rest
        except yaml.YAMLError:
            return {}, content
    return {}, content

def get_existing_tags(fm):
    tags = set()
    raw = fm.get('tags', [])
    if isinstance(raw, str):
        tags.add(raw.strip())
    elif isinstance(raw, list):
        for t in raw:
            if t:
                tags.add(str(t).strip())
    return tags

def has_frontmatter(content):
    return bool(re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL))

def build_frontmatter_lines(fm, tags):
    lines = ['---']
    
    for k, v in fm.items():
        if k == 'tags':
            continue
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                if isinstance(item, str) and '\n' in item:
                    lines.append(f"  - \"{item}\"")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(v, dict):
            lines.append(f"{k}:")
            for sk, sv in v.items():
                lines.append(f"  {sk}: {sv}")
        elif v is None:
            lines.append(f"{k}:")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        else:
            lines.append(f"{k}: {v}")
    
    sorted_tags = sorted(tags)
    lines.append("tags:")
    for t in sorted_tags:
        lines.append(f"  - {t}")
    
    lines.append('---')
    return lines

def rebuild_content(fm, tags, rest):
    fm_lines = build_frontmatter_lines(fm, tags)
    fm_str = '\n'.join(fm_lines) + '\n'
    stripped = rest.lstrip('\n')
    return fm_str + stripped

def process_archive(rel_path):
    p = str(rel_path)
    if p == 'Archive/Home.md':
        return {'#area/personal', '#type/doc', '#status/archived'}
    elif '_trash/' in p:
        return {'#area/personal', '#type/note', '#status/archived'}
    elif 'eKids' in p:
        return {'#area/learning', '#type/doc', '#status/archived'}
    elif 'BalansePRO/' in p:
        return {'#area/work', '#type/doc', '#status/archived'}
    elif 'Busines/' in p:
        return {'#area/work', '#type/note', '#status/archived'}
    elif 'Process Navigation/' in p:
        return {'#area/work', '#type/doc', '#status/archived'}
    else:
        return {'#area/work', '#type/doc', '#status/archived'}

def process_education(rel_path):
    return {'#area/learning', '#type/doc'}

def process_fation_ai(rel_path):
    p = str(rel_path)
    if 'adr/' in p:
        return {'#area/work', '#type/adr'}
    elif 'api/' in p:
        return {'#area/work', '#type/doc'}
    elif 'payments/' in p:
        return {'#area/work', '#type/doc'}
    elif 'operations/' in p:
        return {'#area/work', '#type/runbook'}
    elif 'product/' in p:
        return {'#area/work', '#type/spec'}
    elif 'runbooks/' in p:
        return {'#area/work', '#type/runbook'}
    elif '_templates/' in p:
        return {'#area/work', '#type/template'}
    elif 'meta/' in p:
        return {'#area/work', '#type/doc'}
    else:
        return {'#area/work', '#type/doc'}

def main():
    processors = {
        'Archive': process_archive,
        'Education': process_education,
        'fation-ai': process_fation_ai,
    }
    
    results = []
    total_modified = 0
    
    for arch, processor in processors.items():
        base = VAULT / arch
        if not base.exists():
            results.append(f"⚠ WARNING: {base} does not exist, skipping")
            continue
        
        results.append(f"\n{'='*60}")
        results.append(f"📁 Processing: {arch}/")
        
        for filepath in sorted(base.rglob('*.md')):
            rel_path = filepath.relative_to(VAULT)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    results.append(f"  ⚠ Empty: {rel_path}")
                    continue
                
                existing_has_fm = has_frontmatter(content)
                
                if not existing_has_fm:
                    desired_tags = processor(rel_path)
                    fm_lines = ['---']
                    sorted_tags = sorted(desired_tags)
                    fm_lines.append("tags:")
                    for t in sorted_tags:
                        fm_lines.append(f"  - {t}")
                    fm_lines.append('---')
                    new_content = '\n'.join(fm_lines) + '\n\n' + content.strip()
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    results.append(f"  ✚ {rel_path} -> tags: {', '.join(sorted(desired_tags))}")
                    total_modified += 1
                    continue
                
                fm, rest = parse_frontmatter(content)
                existing_tags = get_existing_tags(fm)
                desired_tags = processor(rel_path)
                
                # Preserve existing tags not in #area/, #type/, #status/ hierarchy
                preserved_tags = set()
                for t in existing_tags:
                    if not any(t.startswith(p) for p in ['#area/', '#type/', '#status/']):
                        preserved_tags.add(t)
                
                all_tags = desired_tags | preserved_tags
                
                if existing_tags == all_tags:
                    continue
                
                new_content = rebuild_content(fm, all_tags, rest)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                added = sorted(all_tags - existing_tags)
                results.append(f"  ✓ {rel_path} +{', '.join(added)}")
                total_modified += 1
                
            except Exception as e:
                results.append(f"  ✗ ERROR {rel_path}: {e}")
    
    results.append(f"\n{'='*60}")
    results.append(f"📊 Total modified: {total_modified} files")
    results.append(f"{'='*60}")
    
    report = '\n'.join(results)
    print(report)
    
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nReport saved to {REPORT}")

if __name__ == '__main__':
    main()
