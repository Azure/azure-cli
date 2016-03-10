import os.path
from codecs import open as codecs_open

_translations = dict()
_locale_dir = ''

def L(key):
    # Not localizing for now, so don't print an error message if text is un-localized
    return _translations.get(key) or key

def install(locale_dir):
    mapping = []

    with codecs_open(os.path.join(locale_dir, "messages.txt"), 'r', encoding='utf-8-sig') as f:
        for i in f:
            if not i or i.startswith('#') or not i.strip():
                continue
            if i.startswith('KEY: '):
                mapping.append((i[5:].strip(), None))
            else:
                mapping[-1] = (mapping[-1][0], i.strip())

    globals()['_translations'] = dict(mapping)
    globals()['_locale_dir'] = locale_dir

def get_file(name):
    try:
        src = _locale_dir
    except (NameError, AttributeError):
        raise RuntimeError("localizations not installed")

    return os.path.join(src, name)
