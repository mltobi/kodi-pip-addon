#!/usr/bin/python3

'''
Copyright (C) 2021 mltobi

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

try:
    from lxml import etree
except ImportError:
    pass

'''
Class Keymap
creates and updates keymap xml file
'''
class Keymap:

    # constructor
    def __init__(self, path):
        self.path = path


    # update keys
    def update(self, keyToggle, keyBack, keyUp, keyDown):
        self.keyActions = [
            {'action': 'toggle_pip',       'key': keyToggle},
            {'action': 'channel_back_pip', 'key': keyBack},
            {'action': 'channel_up_pip',   'key': keyUp},
            {'action': 'channel_down_pip', 'key': keyDown}]


    # create keymap xml file 
    def create(self):

        # create root element
        try:
            elRoot = etree.Element('keymap')
        except NameError:
            pass
        
        # create sub element
        elGlobal = etree.Element('global')
        elRoot.append(elGlobal)

        elKeyboard = etree.Element('keyboard')
        elGlobal.append(elKeyboard)

        # create sub element to keyboard for each key
        for item in self.keyActions:
            
            # split setting string
            parts = item['key'].split('+')

            # create key element
            elKey = etree.Element(parts[-1])

            # add mod attribute to key element
            if len(parts) > 1:
                elKey.attrib['mod'] = ','.join(parts[:-1])

            # add action content to key element
            elKey.text = 'NotifyAll(service.pip, %s)' % item['action']

            # add key element to keyboard
            elKeyboard.append(elKey)

        # create xml string
        s = etree.tostring(elRoot, pretty_print=True)

        # write strint to file
        fobj = open(self.path + '/' + 'pipkeymap.xml', 'wb')
        fobj.write(s)
        fobj.close()

