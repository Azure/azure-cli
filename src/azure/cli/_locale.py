import os.path

from codecs import open

def install(locale_dir):
    mapping = []
    
    with open(os.path.join(locale_dir, "messages.txt"), 'r', encoding='utf-8-sig') as f:
        for i in f:
            if not i or i.startswith('#') or not i.strip():
                continue
            if i.startswith('KEY: '):
                mapping.append((i[5:].strip(), None))
            else:
                mapping[-1] = (mapping[-1][0], i.strip())
    
    translations = dict(mapping)
    def _(key):
        # no warning for unlocalized strings right now because we are currently not localizing
        return translations.get(key) or key
    _.locale_dir = locale_dir
    
    __builtins__['_'] = _

def get_file(name):
    try:
        src = _.locale_dir
    except (NameError, AttributeError):
        raise RuntimeError("localizations not installed")
    
    return os.path.join(src, name)
