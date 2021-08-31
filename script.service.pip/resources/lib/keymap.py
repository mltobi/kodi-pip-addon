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

import xml.dom.minidom as xml

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

        # create new xml document
        doc = xml.Document();

        # add root element
        elKeymap = doc.createElement('keymap')
        doc.appendChild(elKeymap)

        # create sub elements
        elGlobal = doc.createElement('global')
        elKeymap.appendChild(elGlobal)
        elKeyboard = doc.createElement('keyboard')
        elGlobal.appendChild(elKeyboard)

        # create sub element to keyboard for each key
        for item in self.keyActions:

            # split setting string
            parts = item['key'].split('+')

            # create key element
            elKey = doc.createElement(parts[-1])
            elKeyboard.appendChild(elKey)

            # add mod attribute to key element
            if len(parts) > 1:
                elKey.setAttribute('mod', ','.join(parts[:-1]))

            # add action content to key element
            elKey.appendChild(doc.createTextNode('NotifyAll(service.pip, %s)' % item['action']))

        # create xml string
        s = doc.toprettyxml(indent="  ", newl="\n")

        # write strint to file
        fobj = open(self.path + '/' + 'pipkeymap.xml', 'w')
        fobj.write(s)
        fobj.close()

