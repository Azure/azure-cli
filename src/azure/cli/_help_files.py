from yaml import load

def _load_help_file(delimiters):
    helps = {'login': """
    type: command
    short-summary: this module does xyz one-line or so
    long-summary: |
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2
    parameters: 
        - name: --username/-u
          type: string
          required: True
          short-summary: one line partial sentence
          long-summary: text, markdown, etc.
          populator-commands: 
              - az vm list
              - default
        - name: --service-principal
          type: string
          short-summary: one line partial sentence
          long-summary: paragraph(s)
        - name: --tenant/-t
          type: string
          short-summary: one line partial sentence
          long-summary: paragraph(s)
    examples:
        - name: foo example
          text: example details
    """,
    'account': """
        type: group
        short-summary: this module does xyz one-line or so
        long-summary: |
            this module.... kjsdflkj... klsfkj paragraph1
            this module.... kjsdflkj... klsfkj paragraph2
        parameters: 
            - name: --username/-u
              type: string
              required: false
              short-summary: one line partial sentence
              long-summary: text, markdown, etc.
              populator-commands: 
                  - az vm list
                  - default
            - name: --password/-p
              type: string
              short-summary: one line partial sentence
              long-summary: paragraph(s)
            - name: --service-principal
              type: string
              short-summary: one line partial sentence
              long-summary: paragraph(s)
            - name: --tenant/-t
              type: string
              short-summary: one line partial sentence
              long-summary: paragraph(s)
        examples:
            - name: foo example
              text: example details
    """,
    'azure-cli': 'detailed intro help'
    }

    if delimiters in helps:
        return load(helps[delimiters])
    else:
        return None
