import yaml

def _load_help_file(delimiters):
    helps = {'test_group1.test_group2': """
                type: group
                short-summary: this module does xyz one-line or so
                long-summary: |
                    this module.... kjsdflkj... klsfkj paragraph1
                    this module.... kjsdflkj... klsfkj paragraph2
                examples:
                    - name: foo example
                      text: example details
             """
            }

    if delimiters in helps:
        return yaml.load(helps[delimiters])
    else:
        return None
