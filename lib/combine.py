import json
import os
import re
import string
import sys

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SOURCES_DIR = os.path.join(BASE_DIR, 'sources')

TYPE_LABELS = {1: 'container', 2: 'swarm', 3: 'stack', 4: 'edge'}

reset_color = "\033[0m"
def rgb(r, g, b):
  return f"\033[38;2;{r};{g};{b}m"

def normalize_string(original, lowercase=True):
  normalized = original.translate(str.maketrans('', '', string.punctuation)).replace(' ', '')
  return normalized.lower() if lowercase else normalized.capitalize()

CATEGORY_ACRONYMS = {'ai', 'vpn', 'iot', 'nas', 'dns', 'ci', 'cd', 'tv', 'os', 'ip', 'sql',
                     'api', 'cms', 'ftp', 'rss', 'cctv', 'llm', 'osint', 'pdf', '3d'}

def normalize_category(c):
  """Split a category into words and title-case it for display"""
  words = [w for w in re.split(r'[^0-9a-zA-Z]+', c) if w]
  label = ' '.join(w.upper() if w.lower() in CATEGORY_ACRONYMS else w.capitalize()
                   for w in words)
  return 'edge' if label == 'Edge' else label

def template_score(t):
  """Score a template's completeness. Higher is more complete."""
  score = len(t)  # number of top-level keys
  score += len(t.get('env', []))
  score += len(t.get('volumes', []))
  score += len(t.get('ports', []))
  return score

def load_sources():
  """Load and merge all template JSON files from sources/local/ and sources/external/."""
  templates = []
  local_dir = os.path.join(SOURCES_DIR, 'local')
  external_dir = os.path.join(SOURCES_DIR, 'external')
  for is_local, d in [(True, local_dir), (False, external_dir)]:
    if not os.path.isdir(d):
      continue
    for file in sorted(os.listdir(d)):
      file_path = os.path.join(d, file)
      if not (os.path.isfile(file_path) and file.endswith('.json')):
        continue
      with open(file_path) as f:
        try:
          source_templates = json.load(f)['templates']
        except (json.decoder.JSONDecodeError, KeyError) as err:
          print(f'{rgb(255, 0, 0)}Skipping source due to error:{reset_color} {f.name}')
          print(f'Error: {err}')
          continue
      for t in source_templates:
        t['_source'] = file
        t['_local'] = is_local
      templates += source_templates
  return templates

VALID_ENV_KEYS = {'name', 'label', 'description', 'default', 'preset', 'select'}

def normalize_template_fields(templates):
  """Fix non-standard field names and malformed entries from upstream sources."""
  for t in templates:
    # Merge singular 'category' into 'categories'
    if 'category' in t:
      existing = t.get('categories', [])
      merged = list(dict.fromkeys(existing + t.pop('category')))
      t['categories'] = merged

    # Convert legacy v2 edge templates (type 4 with a stackfile URL) to compose stacks
    if t.get('type') == 4 and isinstance(t.get('stackfile'), str):
      m = re.match(r'https://raw\.githubusercontent\.com/([^/]+/[^/]+)/[^/]+/(.+)', t.pop('stackfile'))
      if m:
        t['type'] = 3
        t['repository'] = {'url': f'https://github.com/{m[1]}', 'stackfile': m[2]}
        t.setdefault('categories', ['edge'])

    # Fix env vars
    if 'env' in t:
      cleaned_env = []
      for env in t['env']:
        # Filter malformed entries (entire templates nested in env arrays)
        if not isinstance(env.get('name'), str) or any(k in env for k in ('categories', 'repository', 'logo')):
          continue
        # Convert non-standard 'set' to 'default' + 'preset'
        if 'set' in env and 'default' not in env:
          env['default'] = env.pop('set')
          env.setdefault('preset', True)
        elif 'set' in env:
          del env['set']
        cleaned_env.append({k: v for k, v in env.items() if k in VALID_ENV_KEYS})
      t['env'] = cleaned_env

    # Drop malformed leading ':' from port mappings (e.g. ':80/tcp')
    if 'ports' in t:
      t['ports'] = [p.lstrip(':') for p in t['ports']]

    if isinstance(t.get('maintainer'), str):
      t['maintainer'] = t['maintainer'].strip()

    t.pop('devices', None)  # not part of the Portainer template spec

    # Fix volume 'read_only' -> 'readonly' (and coerce to bool)
    for vol in t.get('volumes', []):
      if 'read_only' in vol:
        val = vol.pop('read_only')
        vol['readonly'] = val if isinstance(val, bool) else str(val).lower() == 'true'

def is_valid_template(t):
  """Check a template has the required fields for its type."""
  if not isinstance(t.get('title'), str) or not isinstance(t.get('description'), str):
    return False
  tmpl_type = t.get('type', 1)
  if not isinstance(tmpl_type, int):
    return False
  if tmpl_type == 1 and 'image' not in t:
    return False
  if tmpl_type in (2, 3) and 'repository' not in t:
    return False
  if tmpl_type == 4 and 'repository' not in t and 'stackFile' not in t:
    return False
  return True

def deduplicate_and_normalize(templates):
  """Filter invalid, deduplicate by (title, type) keeping best version, and normalize category names."""
  best = {}
  for t in templates:
    if not is_valid_template(t):
      print(f'{rgb(255, 165, 0)}Skipping invalid template:{reset_color} {t.get("title", "<no title>")}')
      continue
    key = (normalize_string(t['title']), t.get('type', 1))
    t_is_local = t.get('_local', False)
    t_score = template_score(t)
    if key in best:
      existing = best[key]
      existing_is_local = existing.get('_local', False)
      existing_score = template_score(existing)
      # Local always beats non-local; among same locality, higher score wins
      if t_is_local and not existing_is_local:
        best[key] = t
      elif not t_is_local and existing_is_local:
        pass  # keep existing
      elif t_score > existing_score:
        best[key] = t
    else:
      best[key] = t
  result = []
  for t in best.values():
    cats = {}
    for c in t.get('categories', []):
      label = normalize_category(c)
      if label:
        cats.setdefault(label.lower(), label)
    t['categories'] = list(cats.values())
    result.append(t)
  return result

def postfix_ambiguous_titles(templates):
  """Append type labels to titles that appear with multiple types."""
  from collections import Counter

  # Pass 1: postfix titles that share a normalized name across different types
  title_counts = Counter(normalize_string(t['title']) for t in templates)
  ambiguous = {title for title, count in title_counts.items() if count > 1}
  for t in templates:
    if normalize_string(t['title']) in ambiguous:
      tmpl_type = t.get('type', 1)
      label = TYPE_LABELS.get(tmpl_type, f'type{tmpl_type}')
      t['title'] = f"{t['title']} ({label})"

  # Pass 2: postfix any NEW collisions created by pass 1
  post_counts = Counter(normalize_string(t['title']) for t in templates)
  new_ambiguous = {title for title, count in post_counts.items() if count > 1}
  for t in templates:
    if normalize_string(t['title']) in new_ambiguous and not t['title'].endswith(')'):
      tmpl_type = t.get('type', 1)
      label = TYPE_LABELS.get(tmpl_type, f'type{tmpl_type}')
      t['title'] = f"{t['title']} ({label})"

if __name__ == '__main__':
  raw = load_sources()
  normalize_template_fields(raw)
  templates = deduplicate_and_normalize(raw)
  postfix_ambiguous_titles(templates)
  # Strip internal tags
  for t in templates:
    t.pop('_source', None)
    t.pop('_local', None)
  templates.sort(key=lambda t: t['title'].lower())
  for i, t in enumerate(templates, start=1):
    t['id'] = i
  out_path = os.path.join(BASE_DIR, 'templates.json')
  try:
    with open(out_path) as f:
      previous = len(json.load(f)['templates'])
  except (OSError, ValueError, KeyError):
    previous = 0
  # A failed source download must not silently shrink the published list
  if len(templates) < previous * 0.9 and not os.environ.get('ALLOW_SHRINK'):
    sys.exit(f'Refusing to write: template count fell from {previous} to {len(templates)}. '
             'Set ALLOW_SHRINK=1 if this is intentional.')
  output = {'version': '3', 'templates': templates}
  with open(out_path, 'w') as f:
    json.dump(output, f, indent=2, sort_keys=False)
