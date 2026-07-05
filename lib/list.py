import json
import html
import urllib.parse
import os
import csv
import re
import sys

from log import get_logger, banner

log = get_logger()

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
readme_path = os.path.join(project_dir, '.github/README.md')
templates_path = os.path.join(project_dir, 'templates.json')
sources_path = os.path.join(project_dir, 'sources.csv')

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def load_csv_file(file_path):
    with open(file_path, 'r') as file:
        return list(csv.reader(file))

def slugify(title: str):
    baseUrl = 'https://portainer-templates.as93.net'
    slug = re.sub(r'\s+', '-', re.sub(r'[^a-z0-9 ]', '', title.lower()).strip())
    return f'{baseUrl}/{slug}'

def clean_text(text):
    """Remove quotes/brackets and duplicate whitespace for html/md render"""
    text = (text or '').replace('"', '”').replace("'", '’').replace('<', '').replace('>', '')
    return re.sub(r'\s+', ' ', text).strip()

def generate_app_list():
  templates = load_json_file(templates_path)['templates']
  templates.sort(key=lambda template: template['title'].lower())
  markdown_content = ''
  for index, template in enumerate(templates):
      name = template['title']
      maintainer = template.get('maintainer')
      maintainer_md_link = f" -- ([Report issues]({maintainer}))" if maintainer else ''
      description = clean_text(template['description'])
      if 'logo' in template and template['logo']:
          logo = f"<img title=\"{description}\" src=\"{html.escape(template['logo'])}\" width='26' height='26' /> "
      else:
          logo = ' '
      markdown_content += f"{index+1}. {logo}**[{name}]({slugify(name)} '{description}')** {maintainer_md_link}\n"
  return markdown_content

def generate_sources_list():
    sources = load_csv_file(sources_path)
    markdown_content = ''

    count = 0
    for source in sources:
        if len(source) > 1 and source[1].strip():
          count += 1
          url = source[1].strip()
          parsed_url = urllib.parse.urlparse(url)
          path_parts = [p for p in parsed_url.path.split('/') if p]
          if parsed_url.hostname in ('github.com', 'raw.githubusercontent.com') and path_parts:
            username = path_parts[0]
            avatar = f'<img src="https://github.com/{username}.png?size=40" width="26" height="26" />'
            markdown_content += f"{count}. {avatar} [template]({url}) by [@{username}](https://github.com/{username})\n"
          else:
            markdown_content += f"{count}. [template]({url})\n"

    return markdown_content

def insert_content_between_markers(file_path, start_marker, end_marker, content_to_insert):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    start_index = -1
    end_index = -1

    for i, line in enumerate(lines):
        if start_marker in line:
            start_index = i
        if end_marker in line:
            end_index = i
            break

    if start_index < 0 or end_index <= start_index:
        log.error(f'Markers {start_marker} / {end_marker} not found in {file_path}')
        sys.exit(1)

    lines[start_index + 1:end_index] = [content_to_insert + '\n']

    with open(file_path, 'w') as file:
        file.writelines(lines)

banner('List', 'Render app + source lists into the README')

# Insert sources list into readme
sources_md = generate_sources_list()
insert_content_between_markers(
  readme_path,
  '<!-- auto-insert-sources:start -->',
  '<!-- auto-insert-sources:end -->',
  sources_md,
)
log.info(f'Rendered {sources_md.count(chr(10))} sources into README')

# Insert app list into readme
apps_md = generate_app_list()
insert_content_between_markers(
  readme_path,
  '<!-- auto-insert-apps:start -->',
  '<!-- auto-insert-apps:end -->',
  apps_md,
)
log.info(f'Rendered {apps_md.count(chr(10))} apps into README')
