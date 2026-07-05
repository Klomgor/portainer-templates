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
        return

    # Add maintainer field to each template
    for t in sourceJson.get('templates', []):
        t['maintainer'] = maintainer

    print('saving to', os.path.abspath(file_path))
    with open(file_path, 'w') as f:
        json.dump(sourceJson, f, indent=2, sort_keys=False)

# Gets list of URLs to download from CSV file
def get_source_list():
  sources=[]
  with open(sources_list, mode='r') as file:
      csvFile = csv.reader(file)
      for lines in csvFile:
        if len(lines) > 2 and lines[1].strip():
          sources.append([col.strip() for col in lines])
  return sources

# Create destination folder if not yet present
if not os.path.exists(destination_dir):
  os.makedirs(destination_dir)

# For each source, download the templates JSON file
for sourceUrl in get_source_list():
  download(sourceUrl[1], sourceUrl[0] + '.json', sourceUrl[2])
