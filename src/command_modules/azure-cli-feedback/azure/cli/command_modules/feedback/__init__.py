from __future__ import print_function
from six.moves import input #pylint: disable=redefined-builtin
from azure.cli.commands import cli_command

MESSAGES = {
    'intro': 'We appreciate your feedback!',
    'prompt_how_likely': '\nHow likely is it you would recommend our Azure CLI to a friend or '\
    'colleague? [0 to 10]: ',
    'prompt_what_changes': '\nWhat changes would we have to make for you to give us a higher '\
    'rating? ',
    'prompt_do_well': '\nWhat do we do really well? ',
    'prompt_email_addr': '\nIf you would be open to providing more feedback, '\
    'let us know by leaving your email address (leave blank to skip): '
}

def _prompt_likely_score():
    while True:
        try:
            likely_score = int(input(MESSAGES['prompt_how_likely']))
            if 0 <= likely_score <= 10:
                return likely_score
        except ValueError:
            pass

def handle_feedback():
    try:
        print(MESSAGES['intro'])
        likely_score = _prompt_likely_score()
        if likely_score == 10:
            response = input(MESSAGES['prompt_do_well'])
        else:
            response = input(MESSAGES['prompt_what_changes'])
        email_address = input(MESSAGES['prompt_email_addr'])
        # TODO Send data to app insights (likely_score, response, email)
        print(response, email_address)
    except KeyboardInterrupt:
        # Catch to prevent stacktrace and print newline
        print()

cli_command('feedback', handle_feedback)
