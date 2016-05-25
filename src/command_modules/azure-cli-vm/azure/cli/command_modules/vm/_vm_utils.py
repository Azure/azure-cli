from codecs import open as codecs_open
import json
import os

def read_content_if_is_file(string_or_file):
    content = string_or_file
    if os.path.exists(string_or_file):
        with open(string_or_file, 'r') as f:
            content = f.read()
    return content

def load_json(string_or_file_path):
    if os.path.exists(string_or_file_path):
        return _load_json_from_file(string_or_file_path, 'utf-8') \
            or _load_json_from_file(string_or_file_path, 'utf-8-sig') \
            or _load_json_from_file(string_or_file_path, 'utf-16') \
            or _load_json_from_file(string_or_file_path, 'utf-16le') \
            or _load_json_from_file(string_or_file_path, 'utf-16be')
    else:
        return json.loads(string_or_file_path)

def _load_json_from_file(file_path, encoding):
    try:
        with codecs_open(file_path, encoding=encoding) as f:
            text = f.read()
        return json.loads(text)
    except ValueError:
        pass

