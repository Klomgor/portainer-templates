"""Generates .github/changelog.json - what changed between each version tag.

Walks every vMAJOR.MINOR.PATCH tag in version order, diffs the compiled
templates.json between consecutive tags, and records the templates added,
removed and updated in each version. Rebuilt from scratch on every run, so
the output is deterministic (safe to re-run, self-heals, no commit churn).

Matches the diff semantics of the release notes in release.yml: templates
are keyed by title, with `id` ignored (it renumbers on every regeneration,
which would otherwise flag everything as updated).
"""
import json
import os
import re
import subprocess
import sys

from log import get_logger, banner

log = get_logger()

SEMVER_TAG = re.compile(r'^v\d+\.\d+\.\d+$')

# Pre-v1.0.0 tags predate the current release cadence, so their diffs are
# just a giant re-listing of everything. Start the changelog at v1.0.0
FIRST_VERSION = (1, 0, 0)

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(script_dir, '..')
output_path = os.path.join(root_dir, '.github', 'changelog.json')

def git(*args):
    """Run a git command in the repo root and return its stdout"""
    result = subprocess.run(
        ['git', *args], capture_output=True, text=True, check=True, cwd=root_dir)
    return result.stdout

def version(tag):
    """Numeric (major, minor, patch) tuple for a vX.Y.Z tag"""
    return tuple(int(p) for p in tag[1:].split('.'))

def semver_tags():
    """All vMAJOR.MINOR.PATCH tags from FIRST_VERSION onwards, oldest first"""
    tags = [t for t in git('tag').splitlines() if SEMVER_TAG.match(t)]
    return sorted((t for t in tags if version(t) >= FIRST_VERSION), key=version)

def tag_dates():
    """Map of tag -> creation date (YYYY-MM-DD)"""
    lines = git('for-each-ref', '--format=%(refname:short) %(creatordate:short)',
                'refs/tags').splitlines()
    return dict(line.split(' ', 1) for line in lines if ' ' in line)

def templates_at(tag):
    """Templates in templates.json at a tag, keyed by title with `id` dropped.
    Returns None if the file doesn't exist at that tag."""
    try:
        raw = git('show', f'{tag}:templates.json')
    except subprocess.CalledProcessError:
        return None
    templates = json.loads(raw).get('templates', [])
    return {t['title']: {k: v for k, v in t.items() if k != 'id'}
            for t in templates if isinstance(t, dict) and 'title' in t}

def diff(old, new):
    """Added / removed / updated templates between two title-keyed maps"""
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    updated = []
    for title in sorted(new.keys() & old.keys()):
        if new[title] != old[title]:
            fields = sorted(k for k in new[title].keys() | old[title].keys()
                            if new[title].get(k) != old[title].get(k))
            updated.append({'title': title, 'fields': fields})
    return added, removed, updated

def main():
    banner('Changelog', 'Diff templates.json between version tags')
    tags = semver_tags()
    if not tags:
        log.error('No version tags found (needs full git history, not a shallow clone)')
        sys.exit(1)
    dates = tag_dates()

    entries = []
    previous_tag, previous_map = None, None
    for tag in tags:
        current = templates_at(tag)
        if current is None:
            log.warning(f'{tag}: no templates.json at this tag, skipping')
            continue
        first = previous_map is None
        added, removed, updated = ([], [], []) if first else diff(previous_map, current)
        entries.append({
            'version': tag,
            'previous': previous_tag,
            'date': dates.get(tag),
            'templateCount': len(current),
            'added': added, 'removed': removed, 'updated': updated,
        })
        log.info(f'{tag}: first version ({len(current)} total)' if first else
                 f'{tag}: +{len(added)} added, -{len(removed)} removed, '
                 f'~{len(updated)} updated ({len(current)} total)')
        previous_tag, previous_map = tag, current

    entries.reverse()  # newest first
    with open(output_path, 'w') as file:
        json.dump({'entries': entries}, file, indent=2, ensure_ascii=False)
        file.write('\n')
    log.info(f'Wrote {len(entries)} versions to {os.path.relpath(output_path, root_dir)}')

if __name__ == '__main__':
    main()
