# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import platform

from prompt_toolkit.styles import style_from_dict  # pylint: disable=import-error
from pygments.token import Token  # pylint: disable=import-error


def color_mapping(curr_completion, completion, prompt, command, subcommand,
                  param, text, line, example, toolbar):

    return style_from_dict({
        # Completion colors
        Token.Menu.Completions.Completion.Current: curr_completion,
        Token.Menu.Completions.Completion: completion,
        Token.Menu.Completions.ProgressButton: 'bg:#b78991',
        Token.Menu.Completions.ProgressBar: 'bg:#ffc0cb',

        Token.Az: prompt,
        Token.Prompt.Arg: prompt,

        # Pretty Words
        Token.Keyword: command,
        Token.Keyword.Declaration: subcommand,
        Token.Name.Class: param,
        Token.Text: text,

        Token.Line: line,
        Token.Number: example,
        # toolbar
        Token.Operator: toolbar,
        Token.Toolbar: toolbar
    })


def no_style_wrapper():
    """ wraps for a no colors function """
    return None


def default_style():
    """ Default coloring """
    if platform.system() == 'Windows':
        styles = color_mapping(
            'bg:#7c2c80 #ffffff',
            'bg:#00b7b7 #ffffff',
            '#7c2c80',
            '#965699',
            '#ab77ad',
            '#c49fc5',
            '#0f5050',
            '#E500E5',
            '#00ffff',
            'bg:#000000 #ffffff')

    else:
        styles = color_mapping(
            'bg:#7c2c80 #ffffff',
            'bg:#00b7b7 #ffffff',
            '#7c2c80',
            '#965699',
            '#ab77ad',
            '#c49fc5',
            '#666666',
            '#E500E5',
            '#3d79db',
            'bg:#000000 #ffffff')

    return styles


def quiet_style():
    """ a quiet color palette """
    return color_mapping(
        'bg:#6D929B #ffffff',
        'bg:#00b7b7 #ffffff',
        '#6D929B',
        '#C1DAD6',
        '#ACD1E9',
        '#B7AFA3',
        '#666666',
        '#6D929B',
        '#C1DAD6',
        'bg:#000000 #ffffff')


def purple_style():
    """ a purple palette """
    return color_mapping(
        'bg:#C3C3E5 #ffffff',
        'bg:#8C489F #ffffff',
        '#8C489F',
        '#443266',
        '#443266',
        '#443266',
        '#C3C3E5',
        '#C3C3E5',
        '#C3C3E5',
        'bg:#000000 #ffffff')


def high_contrast_style():
    """ a high contrast palette """
    return color_mapping(
        'bg:#DD1111 #ffffff',
        'bg:#CC0000 #ffffff',
        '#3333FF',
        '#FFCC00',
        '#FFCC00',
        '#FFCC00',
        '#99FF00',
        '#99FF00',
        '#99FF00',
        'bg:#000000 #ffffff')


def pastel_style():
    return color_mapping(
        'bg:#56BAEC #ffffff',
        'bg:#B4D8E7 #ffffff',
        '#FFAEAE',
        '#FFEC94',
        '#FFEC94',
        '#FFEC94',
        '#B4D8E7',
        '#FFF0AA',
        '#FFF0AA',
        'bg:#000000 #ffffff')


def halloween_style():
    """ halloween colors """
    return color_mapping(
        'bg:#7A3E48 #ffffff',
        'bg:#3D3242 #ffffff',
        '#3D3242',
        '#7A3E48',
        '#7A3E48',
        '#B95835',
        '#E18942',
        '#EECD86',
        '#EECD86',
        'bg:#000000 #ffffff',
    )


def grey_style():
    """ a very grey scheme """
    return color_mapping(
        'bg:#555555 #ffffff',
        'bg:#444444 #ffffff',
        '#000044',
        '#000044',
        '#000044',
        '#333333',
        '#222222',
        '#777777',
        '#777777',
        'bg:#000000 #ffffff',
    )


def blue_red_style():
    """ a red and blue ish scheme """
    return color_mapping(
        'bg:#F0ECEB #ffffff',
        'bg:#6C7476 #ffffff',
        '#EE3233',
        '#66A7C5',
        '#66A7C5',
        '#EE3233',
        '#EE3233',
        '#A3D6F5',
        '#A3D6F5',
        'bg:#000000 #ffffff',
    )


def blue_green_style():
    """ a blue green style """
    return color_mapping(
        'bg:#89E894 #ffffff',
        'bg:#BED661 #ffffff',
        '#89E894',
        '#34DDDD',
        '#93E2D5',
        '#78D5E3',
        '#BED661',
        '#7AF5F5',
        '#78D5E3',
        'bg:#ffffff #000000',
    )


def primary_style():
    """ a blue green style """
    return color_mapping(
        'bg:#449adf #ffffff',
        'bg:#002685 #ffffff',
        '#cd1e10',
        '#007e3a',
        '#fe79d1',
        '#4cde77',
        '#763931',
        '#64d13e',
        '#7e77d2',
        'bg:#000000 #ffffff',
    )


def neon_style():
    """ a blue green style """
    return color_mapping(
        'bg:#00ffff #ffffff',
        'bg:#00ff00 #ffffff',
        '#ff0000',
        '#ff00ff',
        '#FD0987',
        '#7920FF',
        '#FF3300',
        '#0000ff',
        '#ff00ff',
        'bg:#FFFF33 #ff0000',
    )


OPTIONS = {
    'quiet': quiet_style,
    'purple': purple_style,
    'default': default_style,
    'none': no_style_wrapper,
    'contrast': high_contrast_style,
    'pastel': pastel_style,
    'halloween': halloween_style,
    'grey': grey_style,
    'br': blue_red_style,
    'bg': blue_green_style,
    'primary': primary_style,
    'neon': neon_style
}


def style_factory(style):
    """ returns the proper style """
    return OPTIONS.get(style, default_style)()


def get_options():
    """ all the color options """
    return OPTIONS.keys()
