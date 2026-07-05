import json
import os
import sys
from jsonschema import Draft7Validator, FormatChecker, ValidationError

from log import get_logger, banner

log = get_logger()

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    banner('Validate', 'Check templates.json against Schema.json')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(script_dir, '..')

    templates = {}
    try:
        schema = load_json_file(os.path.join(root_dir, 'Schema.json'))
        templates = load_json_file(os.path.join(root_dir, 'templates.json'))
        Draft7Validator(schema, format_checker=FormatChecker()).validate(templates)
        log.info('templates.json is valid against the schema')
    except ValidationError as ve:
        log.error(f'Validation error at {ve.json_path}: {ve.message}')
        path = list(ve.absolute_path)
        if path[:1] == ['templates'] and len(path) > 1:
            log.error(f'Title of invalid template: {templates["templates"][path[1]].get("title")}')
        sys.exit(1)
    except FileNotFoundError as fnfe:
        log.error(f'File not found: {fnfe}')
        sys.exit(1)
    except json.JSONDecodeError as jde:
        log.error(f'JSON decoding error: {jde}')
        sys.exit(1)

if __name__ == '__main__':
    main()
