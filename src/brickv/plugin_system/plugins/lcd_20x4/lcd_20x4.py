# -*- coding: utf-8 -*-
"""
LCD 20x4 Plugin
Copyright (C) 2011-2012 Olaf Lüke <olaf@tinkerforge.com>
Copyright (C) 2014, 2016 Matthias Bolte <matthias@tinkerforge.com>

lcd_20x4.py: LCD 20x4 Plugin Implementation

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, \
                            QLineEdit, QComboBox, QFrame

from brickv.plugin_system.plugin_base import PluginBase
from brickv.bindings.bricklet_lcd_20x4 import BrickletLCD20x4
from brickv.bindings.ks0066u import unicode_to_ks0066u
from brickv.async_call import async_call
from brickv.scribblewidget import ScribbleWidget

class LCD20x4(PluginBase):
    MAX_LINE = 4
    MAX_POSITION = 20
    qtcb_pressed = pyqtSignal(int)
    qtcb_released = pyqtSignal(int)

    def __init__(self, *args):
        super().__init__(BrickletLCD20x4, *args)

        self.lcd = self.device

        # the firmware version of a EEPROM Bricklet can (under common circumstances)
        # not change during the lifetime of an EEPROM Bricklet plugin. therefore,
        # it's okay to make final decisions based on it here
        self.has_custom_character = self.firmware_version >= (2, 0, 1)

        self.qtcb_pressed.connect(self.cb_pressed)
        self.lcd.register_callback(self.lcd.CALLBACK_BUTTON_PRESSED,
                                   self.qtcb_pressed.emit)
        self.qtcb_released.connect(self.cb_released)
        self.lcd.register_callback(self.lcd.CALLBACK_BUTTON_RELEASED,
                                   self.qtcb_released.emit)

        self.line_label = QLabel('Line:')
        self.line_combo = QComboBox()

        for i  in range(LCD20x4.MAX_LINE):
            self.line_combo.addItem(str(i))

        self.pos_label = QLabel('Position:')
        self.pos_combo = QComboBox()

        for i in range(LCD20x4.MAX_POSITION):
            self.pos_combo.addItem(str(i))

        self.line_pos_layout = QHBoxLayout()
        self.line_pos_layout.addWidget(self.line_label)
        self.line_pos_layout.addWidget(self.line_combo)
        self.line_pos_layout.addWidget(self.pos_label)
        self.line_pos_layout.addWidget(self.pos_combo)
        self.line_pos_layout.addStretch()

        self.text_label = QLabel('Text:')
        self.text_edit = QLineEdit()
        self.text_edit.setMaxLength(LCD20x4.MAX_POSITION)
        self.text_button = QPushButton('Send Text')
        self.text_layout = QHBoxLayout()
        self.text_layout.addWidget(self.text_label)
        self.text_layout.addWidget(self.text_edit)
        self.text_layout.addWidget(self.text_button)

        self.clear_button = QPushButton("Clear Display")

        self.bl_button = QPushButton()
        self.cursor_button = QPushButton()
        self.blink_button = QPushButton()

        self.onofflayout = QHBoxLayout()
        self.onofflayout.addWidget(self.bl_button)
        self.onofflayout.addWidget(self.cursor_button)
        self.onofflayout.addWidget(self.blink_button)

        self.b0_label = QLabel('Button 0: Released,')
        self.b1_label = QLabel('Button 1: Released,')
        self.b2_label = QLabel('Button 2: Released,')
        self.b3_label = QLabel('Button 3: Released')

        self.buttonlayout = QHBoxLayout()
        self.buttonlayout.addWidget(self.b0_label)
        self.buttonlayout.addWidget(self.b1_label)
        self.buttonlayout.addWidget(self.b2_label)
        self.buttonlayout.addWidget(self.b3_label)

        self.cursor_button.clicked.connect(self.cursor_clicked)
        self.blink_button.clicked.connect(self.blink_clicked)
        self.clear_button.clicked.connect(self.clear_clicked)
        self.bl_button.clicked.connect(self.bl_clicked)
        self.text_button.clicked.connect(self.text_clicked)

        if self.has_custom_character:
            line = QFrame()
            line.setObjectName("line")
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)

            self.scribble_widget = ScribbleWidget(5, 8, 25, QColor(Qt.white), QColor(Qt.blue))

            self.char_index_label = QLabel('Index:')
            self.char_index_combo = QComboBox()
            self.char_index_combo.currentIndexChanged.connect(self.char_index_changed)
            for i in range(8):
                self.char_index_combo.addItem(str(i))

            self.char_index_layout = QHBoxLayout()
            self.char_index_layout.addStretch()
            self.char_index_layout.addWidget(self.char_index_label)
            self.char_index_layout.addWidget(self.char_index_combo)
            self.char_index_layout.addStretch()

            self.char_index_save = QPushButton('Save Character')
            self.char_index_save.clicked.connect(self.char_index_save_clicked)
            self.char_show = QPushButton('Show all Custom Characters on LCD')
            self.char_show.clicked.connect(self.show_clicked)
            self.char_save_layout = QVBoxLayout()
            self.char_save_layout.addStretch()
            self.char_save_layout.addLayout(self.char_index_layout)
            self.char_save_layout.addWidget(self.char_index_save)
            self.char_save_layout.addWidget(self.char_show)

            help_label = QLabel('Use "\\0, \\1, ..., \\7" in text field to show custom characters.')
            help_label.setWordWrap(True)

            self.char_save_layout.addWidget(help_label)
            self.char_save_layout.addStretch()

            grid_stretch_layout = QHBoxLayout()
            grid_stretch_layout.addWidget(QLabel('Custom Character:'))
            grid_stretch_layout.addWidget(self.scribble_widget)
            grid_stretch_layout.addLayout(self.char_save_layout)
            grid_stretch_layout.addStretch()

            self.char_main_layout = QHBoxLayout()
            self.char_main_layout.addStretch()
            self.char_main_layout.addLayout(grid_stretch_layout)
            self.char_main_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(self.line_pos_layout)
        layout.addLayout(self.text_layout)
        layout.addWidget(self.clear_button)
        layout.addLayout(self.onofflayout)
        layout.addLayout(self.buttonlayout)

        if self.hardware_version <= (1, 1, 0):
            self.b3_label.hide()

        if self.has_custom_character:
            layout.addWidget(line)
            layout.addLayout(self.char_main_layout)

        layout.addStretch(1)

    def is_backlight_on_async(self, on):
        if on:
            self.bl_button.setText('Backlight Off')
        else:
            self.bl_button.setText('Backlight On')

    def get_config_async(self, config):
        cursor, blink = config
        if cursor:
            self.cursor_button.setText('Cursor Off')
        else:
            self.cursor_button.setText('Cursor On')

        if blink:
            self.blink_button.setText('Blink Off')
        else:
            self.blink_button.setText('Blink On')

    def start(self):
        async_call(self.lcd.is_backlight_on, None, self.is_backlight_on_async, self.increase_error_count)
        async_call(self.lcd.get_config, None, self.get_config_async, self.increase_error_count)

    def stop(self):
        pass

    def destroy(self):
        pass

    def get_url_part(self):
        # override normal get_url_part() function, because the URL part here
        # depends on the hardware version
        return 'lcd_20x4_v{0}{1}'.format(self.hardware_version[0], self.hardware_version[1])

    def is_hardware_version_relevant(self):
        return True

    @staticmethod
    def has_device_identifier(device_identifier):
        return device_identifier == BrickletLCD20x4.DEVICE_IDENTIFIER

    def cb_pressed(self, button):
        if button == 0:
            self.b0_label.setText('Button 0: Pressed,')
        elif button == 1:
            self.b1_label.setText('Button 1: Pressed,')
        elif button == 2:
            self.b2_label.setText('Button 2: Pressed,')
        elif button == 3:
            self.b3_label.setText('Button 3: Pressed')

    def cb_released(self, button):
        if button == 0:
            self.b0_label.setText('Button 0: Released,')
        elif button == 1:
            self.b1_label.setText('Button 1: Released,')
        elif button == 2:
            self.b2_label.setText('Button 2: Released,')
        elif button == 3:
            self.b3_label.setText('Button 3: Released')

    def bl_clicked(self):
        if self.bl_button.text().replace('&', '') == 'Backlight On':
            async_call(self.lcd.backlight_on, None, None, self.increase_error_count)
            self.bl_button.setText('Backlight Off')
        else:
            async_call(self.lcd.backlight_off, None, None, self.increase_error_count)
            self.bl_button.setText('Backlight On')

    def get_config(self):
        cursor = self.cursor_button.text().replace('&', '') == 'Cursor Off'
        blink = self.blink_button.text().replace('&', '') == 'Blink Off'

        return (cursor, blink)

    def cursor_clicked(self):
        cursor, blink = self.get_config()

        async_call(self.lcd.set_config, (not cursor, blink), None, self.increase_error_count)

        if cursor:
            self.cursor_button.setText('Cursor On')
        else:
            self.cursor_button.setText('Cursor Off')

    def blink_clicked(self):
        cursor, blink = self.get_config()

        async_call(self.lcd.set_config, (cursor, not blink), None, self.increase_error_count)

        if blink:
            self.blink_button.setText('Blink On')
        else:
            self.blink_button.setText('Blink Off')

    def clear_clicked(self):
        async_call(self.lcd.clear_display, None, None, self.increase_error_count)

    def text_clicked(self):
        line = int(self.line_combo.currentText())
        position = int(self.pos_combo.currentText())
        text = self.text_edit.text()

        if self.has_custom_character:
            for i in range(8):
                text = text.replace('\\' + str(i), chr(i + 8))

        async_call(self.lcd.write_line, (line, position, unicode_to_ks0066u(text)), None, self.increase_error_count)

    def char_index_save_clicked(self):
        char = [0]*8
        img = self.scribble_widget.image()

        for j in range(img.height()):
            for i in range(img.width() - 1, -1, -1):
                if img.pixel(i, j) == self.scribble_widget.foreground_color().rgb():
                    char[j] |= 1 << (4 - i)

        index = int(self.char_index_combo.currentText())

        async_call(self.lcd.set_custom_character, (index, char), None, self.increase_error_count)

    def show_clicked(self):
        async_call(self.lcd.clear_display, None, None, self.increase_error_count)

        line1 = '0:{0} 1:{1} 2:{2} 3:{3}'.format(chr(8), chr(9), chr(10), chr(11))
        line2 = '4:{0} 5:{1} 6:{2} 7:{3}'.format(chr(12), chr(13), chr(14), chr(15))

        async_call(self.lcd.write_line, (0, 0, line1), None, self.increase_error_count)
        async_call(self.lcd.write_line, (1, 0, line2), None, self.increase_error_count)

    def custom_character_async(self, characters):
        r = []
        g = []
        b = []

        for j in range(self.scribble_widget.image().height()):
            for i in range(self.scribble_widget.image().width() - 1, -1, -1):
                if characters[j] & (1 << i):
                    r.append(255)
                    g.append(255)
                    b.append(255)
                else:
                    r.append(0)
                    g.append(0)
                    b.append(255)

        self.scribble_widget.array_draw(r, g, b)

    def char_index_changed(self, index):
        async_call(self.lcd.get_custom_character, index, self.custom_character_async, self.increase_error_count)
