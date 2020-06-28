import re

def sanitize_github_repository_fullname(github_repository_fullname):
    sanitized_name = re.sub(r"[^A-Za-z0-9_-]|\s", "-", github_repository_fullname)
    return sanitized_name
