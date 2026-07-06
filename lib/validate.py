import json
import os
import sys
from collections import Counter
from jsonschema import Draft7Validator, FormatChecker

from log import get_logger, banner

log = get_logger()

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def check_schema(schema, templates, items):
    """Collect every schema violation, tagged with the offending template's title"""
    errors = []
    for err in Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(templates):
        path = list(err.absolute_path)
        if path[:1] == ['templates'] and len(path) > 1:
            item = items[path[1]]
            title = item.get('title') if isinstance(item, dict) else None
            where = f'#{path[1]} "{title}"' if title else f'#{path[1]}'
        else:
            where = err.json_path
        errors.append(f'{where}: {err.message}')
    return errors

def check_unique(templates, key):
    """Flag any value of `key` shared by more than one template (schema can't)"""
    counts = Counter(t[key] for t in templates if isinstance(t, dict) and key in t)
    return [f'Duplicate {key}: {value!r} appears in {n} templates'
            for value, n in counts.items() if n > 1]

def main():
    banner('Validate', 'Check templates.json against Schema.json')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(script_dir, '..')

    try:
        schema = load_json_file(os.path.join(root_dir, 'Schema.json'))
        templates = load_json_file(os.path.join(root_dir, 'templates.json'))
    except FileNotFoundError as fnfe:
        log.error(f'File not found: {fnfe}')
        sys.exit(1)
    except json.JSONDecodeError as jde:
        log.error(f'JSON decoding error: {jde}')
        sys.exit(1)

    # Schema guards structure; id/title uniqueness guards combine.py invariants the schema can't express
    items = templates.get('templates', []) if isinstance(templates, dict) else []
    log.info(f'Loaded schema and {len(items)} templates')
    steps = {
        'Schema': check_schema(schema, templates, items),
        'Unique ids': check_unique(items, 'id'),
        'Unique titles': check_unique(items, 'title'),
    }

    # Report each step independently; collect a total so one failure still runs the rest
    total = 0
    for name, errors in steps.items():
        if errors:
            total += len(errors)
            for error in errors:
                log.error(f'{name}: {error}')
        else:
            log.info(f'{name} check passed')

    if total:
        log.error(f'templates.json failed validation ({total} issues)')
        sys.exit(1)
    log.info('templates.json is valid')

if __name__ == '__main__':
    main()
