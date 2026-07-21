# -*- coding: utf-8 -*-
# *****************************************************************************
#     Copyright (C) 2006-2020 Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#     Copyright (C) 2020 Bassem Girgis. <brgirgis@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# *****************************************************************************


import System

c32 = System.ConsoleKey

CODE_TO_SYMBOL_MAP = {
    # c32.CANCEL:    'Cancel',
    c32.Backspace: "BackSpace",
    c32.Tab: "Tab",
    c32.Clear: "Clear",
    c32.Enter: "Return",
    # c32.Shift:     'Shift_L',
    # c32.Control:   'Control_L',
    # c32.Menu:      'Alt_L',
    c32.Pause: "Pause",
    # c32.Capital:   'Caps_Lock',
    c32.Escape: "Escape",
    # c32.Space:     'space',
    c32.PageUp: "Prior",
    c32.PageDown: "Next",
    c32.End: "End",
    c32.Home: "Home",
    c32.LeftArrow: "Left",
    c32.UpArrow: "Up",
    c32.RightArrow: "Right",
    c32.DownArrow: "Down",
    c32.Select: "Select",
    c32.Print: "Print",
    c32.Execute: "Execute",
    # c32.Snapshot:  'Snapshot',
    c32.Insert: "Insert",
    c32.Delete: "Delete",
    c32.Help: "Help",
    c32.F1: "F1",
    c32.F2: "F2",
    c32.F3: "F3",
    c32.F4: "F4",
    c32.F5: "F5",
    c32.F6: "F6",
    c32.F7: "F7",
    c32.F8: "F8",
    c32.F9: "F9",
    c32.F10: "F10",
    c32.F11: "F11",
    c32.F12: "F12",
    c32.F13: "F13",
    c32.F14: "F14",
    c32.F15: "F15",
    c32.F16: "F16",
    c32.F17: "F17",
    c32.F18: "F18",
    c32.F19: "F19",
    c32.F20: "F20",
    c32.F21: "F21",
    c32.F22: "F22",
    c32.F23: "F23",
    c32.F24: "F24",
    # c32.Numlock:    'Num_Lock,',
    # c32.Scroll:     'Scroll_Lock',
    # c32.Apps:       'VK_APPS',
    # c32.ProcesskeY: 'VK_PROCESSKEY',
    # c32.Attn:       'VK_ATTN',
    # c32.Crsel:      'VK_CRSEL',
    # c32.Exsel:      'VK_EXSEL',
    # c32.Ereof:      'VK_EREOF',
    # c32.Play:       'VK_PLAY',
    # c32.Zoom:       'VK_ZOOM',
    # c32.Noname:     'VK_NONAME',
    # c32.Pa1:        'VK_PA1',
    c32.OemClear: "VK_OEM_CLEAR",
    c32.NumPad0: "NUMPAD0",
    c32.NumPad1: "NUMPAD1",
    c32.NumPad2: "NUMPAD2",
    c32.NumPad3: "NUMPAD3",
    c32.NumPad4: "NUMPAD4",
    c32.NumPad5: "NUMPAD5",
    c32.NumPad6: "NUMPAD6",
    c32.NumPad7: "NUMPAD7",
    c32.NumPad8: "NUMPAD8",
    c32.NumPad9: "NUMPAD9",
    c32.Divide: "Divide",
    c32.Multiply: "Multiply",
    c32.Add: "Add",
    c32.Subtract: "Subtract",
    c32.Decimal: "VK_DECIMAL",
}

__all__ = [
    "CODE_TO_SYMBOL_MAP",
]
