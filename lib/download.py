import os
import csv
import requests
import json

dir = os.path.dirname(os.path.abspath(__file__))

destination_dir = os.path.join(dir, '../sources/external')
sources_list = os.path.join(dir, '../sources.csv')

# Downloads the templates file from a given URL, to the local destination
def download(url: str, filename: str, maintainer: str):
    file_path = os.path.join(destination_dir, filename)
    print('Downloading', url)
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        sourceJson = r.json()
    except (requests.RequestException, ValueError) as err:
        print(f'Skipping source due to an error: {url}')
        print(f'Error msg: {err}')
        return False

    # Handle sources without valid data
    if isinstance(sourceJson, list):
        sourceJson = {'templates': sourceJson}
    templates = sourceJson.get('templates') if isinstance(sourceJson, dict) else None
    if not isinstance(templates, list) or not templates:
        print(f'Skipping source with no templates: {url}')
        return False

    # Add maintainer field to each template
    for t in templates:
        if isinstance(t, dict) and maintainer:
            t['maintainer'] = maintainer

    print('saving to', os.path.abspath(file_path))
    with open(file_path, 'w') as f:
        json.dump(sourceJson, f, indent=2, sort_keys=False)
    return True

# Gets list of URLs to download from CSV file
def get_source_list():
  sources = []
  seen = set()
  with open(sources_list, mode='r') as file:
      csvFile = csv.reader(file)
      for lines in csvFile:
        row = [col.strip() for col in lines]
        if len(row) < 2 or not row[0] or not row[1]:
          if any(row):
            print(f'Skipping malformed sources.csv row: {lines}')
          continue
        if row[0] in seen:
          print(f'Skipping duplicate source: {row[0]}')
          continue
        seen.add(row[0])
        sources.append(row)
  return sources

# Create destination folder if not yet present
if not os.path.exists(destination_dir):
  os.makedirs(destination_dir)

failures = []
for source in get_source_list():
  if not download(source[1], source[0] + '.json', source[2] if len(source) > 2 else ''):
    failures.append(source[0])

if failures:
  raise SystemExit(f'Failed to download valid sources: {", ".join(failures)}')
