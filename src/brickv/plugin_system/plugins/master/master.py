# -*- coding: utf-8 -*-  
"""
Master Plugin
Copyright (C) 2010-2012 Olaf Lüke <olaf@tinkerforge.com>

master.py: Master Plugin implementation

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

from plugin_system.plugin_base import PluginBase
from bindings.brick_master import BrickMaster
from bindings.ip_connection import IPConnection

from PyQt4.QtGui import QWidget, QFrame, QMessageBox, QFileDialog, QProgressDialog
from PyQt4.QtCore import QTimer, Qt

import os
import time
import sys

from ui_master import Ui_Master
from ui_chibi import Ui_Chibi
from ui_rs485 import Ui_RS485
from ui_wifi import Ui_Wifi
from ui_extension_type import Ui_extension_type
from ui_wifi_status import Ui_widget_wifi_status

from async_call import async_call
import infos

class WifiStatus(QFrame, Ui_widget_wifi_status):
    def __init__(self, parent):
        QFrame.__init__(self, parent, Qt.Popup | Qt.Window | Qt.Tool)
        self.setupUi(self)
        self.parent = parent
        self.master = self.parent.master
        
        self.update_status()
    
    def update_status_async(self, status):
        self.status = status
        mac, bssid, channel, rssi, ip, sub, gw, rx, tx, state = self.status
        
        self.wifi_status_mac.setText("%2.2x:%2.2x:%2.2x:%2.2x:%2.2x:%2.2x" % mac[::-1])
        self.wifi_status_bssid.setText("%2.2x:%2.2x:%2.2x:%2.2x:%2.2x:%2.2x" % bssid[::-1])
        self.wifi_status_channel.setText(str(channel))
        self.wifi_status_rssi.setText(str(rssi) + 'dB')
        self.wifi_status_ip.setText("%d.%d.%d.%d" % ip[::-1])
        self.wifi_status_sub.setText("%d.%d.%d.%d" % sub[::-1])
        self.wifi_status_gw.setText("%d.%d.%d.%d" % gw[::-1])
        self.wifi_status_rx.setText(str(rx))
        self.wifi_status_tx.setText(str(tx))
        
        state_str = "None"
        if state == 0:
            state_str = "Disassociated"
        elif state == 1:
            state_str = "Associated"
        elif state == 2:
            state_str = "Associating"
        elif state == 3:
            state_str = "Startup Error"
        elif state == 255:
            state_str = "No Startup"
            
        self.wifi_status_state.setText(state_str)
    
    def update_status(self):
        async_call(self.master.get_wifi_status, None, self.update_status_async, self.parent.parent.increase_error_count)

class ExtensionTypeWindow(QFrame, Ui_extension_type):
    def __init__(self, parent):
        QFrame.__init__(self, parent, Qt.Popup | Qt.Window | Qt.Tool)
        self.setupUi(self)

        self.setWindowTitle("Configure Extension Type")

        self.parent = parent
        self.master = parent.master
        self.button_type_save.pressed.connect(self.save_pressed)
        self.combo_extension.currentIndexChanged.connect(self.index_changed)

        self.index_changed(0)

    def popup_ok(self):
        QMessageBox.information(self, "Extension Type", "Successfully saved extension type", QMessageBox.Ok)

    def popup_fail(self):
        QMessageBox.critical(self, "Extension Type", "Could not save extension type", QMessageBox.Ok)

    def index_changed_async(self, ext):
        if ext < 0 or ext > (self.type_box.count() - 1):
            ext = 0
        self.type_box.setCurrentIndex(ext)

    def index_changed(self, index):
        async_call(self.master.get_extension_type, index, self.index_changed_async, self.parent.increase_error_count)

    def save_pressed(self):
        extension = self.combo_extension.currentIndex()
        typ = self.type_box.currentIndex()
        try:
            self.master.set_extension_type(extension, typ)
        except:
            self.popup_fail()
            return
        
        try:
            new_type = self.master.get_extension_type(extension)
        except:
            self.popup_fail()
            return
        
        if typ == new_type:
            self.popup_ok()
        else:
            self.popup_fail()
    
class Chibi(QWidget, Ui_Chibi):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.setupUi(self)
        
        self.parent = parent
        self.master = parent.master
        
        if parent.version >= (1, 1, 0):
            self.update_generator = self.init_update()
            self.update_generator.next()
        
    def init_update(self):
        self.update_address = 0
        self.update_chibi_slave_address = 0
        self.update_chibi_master_address = 0
        self.update_chibi_frequency = 0
        self.update_chibi_channel = 0
        
        def get_chibi_address_async(address_async):
            self.update_address = address_async
            self.update_generator.next()
        
        def get_chibi_slave_address_async(chibi_slave_address_async):
            self.update_chibi_slave_address = chibi_slave_address_async
            self.update_generator.next()
            
        def get_chibi_master_address_async(chibi_master_address_async):
            self.update_chibi_master_address = chibi_master_address_async
            self.update_generator.next()
            
        def get_chibi_frequency_async(chibi_frequency_async):
            self.update_chibi_frequency = chibi_frequency_async
            self.update_generator.next()
            
        def get_chibi_channel_async(chibi_channel_async):
            self.update_chibi_channel = chibi_channel_async
            self.update_generator.next()
        
        async_call(self.master.get_chibi_address, None, get_chibi_address_async, self.parent.increase_error_count)
        yield
        
        address_slave = []
        for i in range(32):
            async_call(self.master.get_chibi_slave_address, i, get_chibi_slave_address_async, self.parent.increase_error_count)
            yield
            
            if self.update_chibi_slave_address == 0:
                break
            else:
                address_slave.append(str(self.update_chibi_slave_address))
                
        address_slave_text = ', '.join(address_slave)
        
        async_call(self.master.get_chibi_master_address, None, get_chibi_master_address_async, self.parent.increase_error_count)
        yield
        async_call(self.master.get_chibi_frequency, None, get_chibi_frequency_async, self.parent.increase_error_count)
        yield
        async_call(self.master.get_chibi_channel, None, get_chibi_channel_async, self.parent.increase_error_count)
        yield
        
        typ = 0
        if self.update_address == self.update_chibi_master_address:
            typ = 1
        
        self.lineedit_slave_address.setText(address_slave_text)
        self.address_spinbox.setValue(self.update_address)
        self.master_address_spinbox.setValue(self.update_chibi_master_address)
        self.chibi_frequency.setCurrentIndex(self.update_chibi_frequency)
        self.chibi_channel.setCurrentIndex(self.update_chibi_channel)
        
        self.save_button.pressed.connect(self.save_pressed)
        self.chibi_type.currentIndexChanged.connect(self.chibi_type_changed)
        self.chibi_frequency.currentIndexChanged.connect(self.chibi_frequency_changed)
        self.chibi_channel.currentIndexChanged.connect(self.chibi_channel_changed)
        
        self.chibi_type.setCurrentIndex(typ)
        self.chibi_type_changed(typ)
        self.new_max_count()
        
    def popup_ok(self):
        QMessageBox.information(self, "Configuration", "Successfully saved configuration", QMessageBox.Ok)
    
    def popup_fail(self):
        QMessageBox.critical(self, "Configuration", "Could not save configuration", QMessageBox.Ok)
        
    def new_max_count(self):
        channel = int(self.chibi_channel.currentText())
        self.chibi_channel.currentIndexChanged.disconnect(self.chibi_channel_changed)
        
        for i in range(12):
            self.chibi_channel.removeItem(0)
            
        index = self.chibi_frequency.currentIndex()
        
        if index == 0:
            self.chibi_channel.addItem("0")
            if channel != 0:
                channel = 0
        elif index in (1, 3):
            channel -= 1
            self.chibi_channel.addItem("1")
            self.chibi_channel.addItem("2")
            self.chibi_channel.addItem("3")
            self.chibi_channel.addItem("4")
            self.chibi_channel.addItem("5")
            self.chibi_channel.addItem("6")
            self.chibi_channel.addItem("7")
            self.chibi_channel.addItem("8")
            self.chibi_channel.addItem("9")
            self.chibi_channel.addItem("10")
            if not channel in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
                channel = 0
        elif index == 2:
            self.chibi_channel.addItem("0")
            self.chibi_channel.addItem("1")
            self.chibi_channel.addItem("2")
            self.chibi_channel.addItem("3")
            if not channel in (0, 1, 2, 3):
                channel = 0

        self.chibi_channel.setCurrentIndex(channel)
        self.chibi_channel.currentIndexChanged.connect(self.chibi_channel_changed)
            
    def save_pressed(self):
        typ = self.chibi_type.currentIndex()
        frequency = self.chibi_frequency.currentIndex()
        channel = self.chibi_channel.currentIndex()
        if frequency in (1, 3):
            channel += 1
        address = self.address_spinbox.value()
        address_master = self.master_address_spinbox.value()
        address_slave_text = str(self.lineedit_slave_address.text().replace(' ', ''))
        if address_slave_text == '':
            address_slave = []
        else:
            address_slave = map(int, address_slave_text.split(','))
            address_slave.append(0)
            
        self.master.set_chibi_frequency(frequency)
        self.master.set_chibi_channel(channel)
        self.master.set_chibi_address(address)
        if typ == 0:
            self.master.set_chibi_master_address(address_master)
        else:
            self.master.set_chibi_master_address(address)
            for i in range(len(address_slave)):
                self.master.set_chibi_slave_address(i, address_slave[i])
                
        new_frequency = self.master.get_chibi_frequency()
        new_channel = self.master.get_chibi_channel()
        new_address = self.master.get_chibi_address()
        if typ == 0:
            new_address_master = self.master.get_chibi_master_address()
            if new_frequency == frequency and \
               new_channel == channel and \
               new_address == address and \
               new_address_master == address_master:
                self.popup_ok()
            else:
                self.popup_fail()
        else:
            new_address_master = self.master.get_chibi_master_address()
            new_address_slave = []
            for i in range(len(address_slave)):
                new_address_slave.append(self.master.get_chibi_slave_address(i))
            if new_frequency == frequency and \
               new_channel == channel and \
               new_address == address and \
               new_address_master == address and \
               new_address_slave == address_slave:
                self.popup_ok()
            else:
                self.popup_fail()
                
    def index_changed_async(self, addr):
        self.slave_address_spinbox.setValue(addr)
        
    def index_changed(self, index):
        async_call(self.master.get_chibi_slave_address, index, self.index_changed_async, self.parent.increase_error_count)
        
    def chibi_frequency_changed(self, index):
        self.new_max_count()

    def chibi_channel_changed(self, index):
        channel = int(self.chibi_channel.itemText(index))
        
    def chibi_type_changed(self, index):
        if index == 0:
            self.label_slave_address.hide()
            self.lineedit_slave_address.hide()
            self.label_master_address.show()
            self.master_address_spinbox.show()
        else:
            self.label_master_address.hide()
            self.master_address_spinbox.hide()
            self.label_slave_address.show()
            self.lineedit_slave_address.show()
        
    def signal_strength_update(self, ss):
        ss_str = "%g dBm"  % (ss,)
        self.signal_strength_label.setText(ss_str)
        
    def update_data(self):
        async_call(self.master.get_chibi_signal_strength, None, self.signal_strength_update, self.parent.increase_error_count)
    
class RS485(QWidget, Ui_RS485):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.setupUi(self)
        
        self.parent = parent
        self.master = parent.master
        
        if parent.version >= (1, 2, 0):
            async_call(self.master.get_rs485_configuration, None, self.get_rs485_configuration_async, self.parent.increase_error_count)
            self.update_generator = self.update_addresses()
            self.update_generator.next()

    def update_addresses(self):
        self.update_address = 0
        self.update_address_slave = 0
        
        def get_rs485_address_async(address_async):
            self.update_address = address_async
            self.update_generator.next()
        
        def get_rs485_slave_address_async(update_address_slave_async):
            self.update_address_slave = update_address_slave_async
            self.update_generator.next()
        
        async_call(self.master.get_rs485_address, None, get_rs485_address_async, self.parent.increase_error_count)
        yield
        
        address_slave = []
        for i in range(32):
            async_call(self.master.get_rs485_slave_address, i, get_rs485_slave_address_async, self.parent.increase_error_count)
            yield
            
            if self.update_address_slave == 0:
                break
            else:
                address_slave.append(str(self.update_address_slave))

        address_slave_text = ', '.join(address_slave)

        typ = 0
        if self.update_address == 0:
            typ = 1

            # trigger enumerate for rs485 slaves
            if infos.infos[self.parent.uid].enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED:
                self.parent.ipcon.enumerate()

        self.lineedit_slave_address.setText(address_slave_text)
        self.address_spinbox.setValue(self.update_address)
        
        self.save_button.pressed.connect(self.save_pressed)
        self.rs485_type.currentIndexChanged.connect(self.rs485_type_changed)
        
        self.rs485_type.setCurrentIndex(typ)
        self.rs485_type_changed(typ)
            
    def get_rs485_configuration_async(self, configuration):
        speed, parity, stopbits = configuration
        self.speed_spinbox.setValue(speed)
        if parity == 'e':
            self.parity_combobox.setCurrentIndex(1)
        elif parity == 'o':
            self.parity_combobox.setCurrentIndex(2)
        else:
            self.parity_combobox.setCurrentIndex(0)
        self.stopbits_spinbox.setValue(stopbits)
        

    def destroy(self):
        pass

    def popup_ok(self):
        QMessageBox.information(self, "Configuration", "Successfully saved configuration", QMessageBox.Ok)

    def popup_fail(self):
        QMessageBox.critical(self, "Configuration", "Could not save configuration", QMessageBox.Ok)

    def save_pressed(self):
        speed = self.speed_spinbox.value()
        parity_index = self.parity_combobox.currentIndex()
        parity = 'n'
        if parity_index == 1:
            parity = 'e'
        elif parity_index == 2:
            parity = 'o'
        stopbits = self.stopbits_spinbox.value()
          
        self.master.set_rs485_configuration(speed, parity, stopbits)
        
        typ = self.rs485_type.currentIndex()
        if typ == 0:
            address = self.address_spinbox.value()
        else:
            address = 0
            
        address_slave_text = str(self.lineedit_slave_address.text().replace(' ', ''))
        if address_slave_text == '':
            address_slave = []
        else:
            address_slave = map(int, address_slave_text.split(','))
            address_slave.append(0)
            
        self.master.set_rs485_address(address)
        if typ == 1:
            for i in range(len(address_slave)):
                self.master.set_rs485_slave_address(i, address_slave[i])
                
        new_address = self.master.get_rs485_address()
        if typ == 0:
            if new_address == address:
                self.popup_ok()
            else:
                self.popup_fail()
        else:
            new_address_slave = []
            for i in range(len(address_slave)):
                new_address_slave.append(self.master.get_rs485_slave_address(i))
            if new_address == 0 and new_address_slave == address_slave:
                self.popup_ok()
            else:
                self.popup_fail()
        
    def rs485_type_changed(self, index):
        if index == 0:
            self.label_slave_address.hide()
            self.lineedit_slave_address.hide()
            self.label.show()
            self.address_spinbox.show()
        else:
            self.label_slave_address.show()
            self.lineedit_slave_address.show()
            self.label.hide()
            self.address_spinbox.hide()
            
    def update_data(self):
        pass

class Wifi(QWidget, Ui_Wifi):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.setupUi(self)
        self.parent = parent
        self.master = parent.master
        
        self.update_data_counter = 0
        self.connection = 0
        if parent.version >= (1, 3, 0):
            if parent.version < (1, 3, 3):
                # AP and Ad Hoc was added in 1.3.3
                while self.wifi_connection.count() > 2:
                    self.wifi_connection.removeItem(self.wifi_connection.count() - 1)
                    
            async_call(self.master.get_wifi_configuration, None, self.get_wifi_configuration_async, self.parent.increase_error_count)
            async_call(self.master.get_wifi_certificate, 0xFFFF, self.update_username_async, self.parent.increase_error_count)
            async_call(self.master.get_wifi_certificate, 0xFFFE, self.update_password_async, self.parent.increase_error_count)
            async_call(self.master.get_wifi_power_mode, None, self.wifi_power_mode.setCurrentIndex, self.parent.increase_error_count)
            
            if parent.version >= (1, 3, 4):
                async_call(self.master.get_wifi_regulatory_domain, None, self.wifi_domain.setCurrentIndex, self.parent.increase_error_count)
            else:
                self.wifi_domain.setEnabled(0)
                self.wifi_domain.clear()
                self.wifi_domain.addItem("Master Firmware > 1.3.3 needed")
            
            async_call(self.master.get_wifi_encryption, None, self.get_wifi_encryption_async, self.parent.increase_error_count)

            self.wifi_status = None

    def update_username_async(self, username):
        username = ''.join(map(chr, username[0][:username[1]]))
        self.wifi_username.setText(username)
        
    def update_password_async(self, password):
        password = ''.join(map(chr, password[0][:password[1]]))
        self.wifi_password.setText(password)

    def get_long_wifi_key_async(self, key):
        self.wifi_key.setText(key)

    def get_wifi_encryption_async(self, enc):
        encryption, key, key_index, eap_options, ca_certificate_length, client_certificate_length, private_key_length = enc
        
        if self.connection in (2, 3, 4, 5):
            encryption -= 2
            
        eap_outer = eap_options & 0b00000011
        eap_inner = (eap_options & 0b00000100) >> 2
        key = key.replace('\0', '')
        
        self.wifi_eap_outer_auth.setCurrentIndex(eap_outer)
        self.wifi_eap_inner_auth.setCurrentIndex(eap_inner)
        self.wifi_encryption.setCurrentIndex(encryption)

        if key == '-' and self.parent.version >= (2, 0, 2):
            async_call(self.master.get_long_wifi_key, None, self.get_long_wifi_key_async, self.parent.increase_error_count)
        else:
            self.wifi_key.setText(key)

        self.wifi_key_index.setValue(key_index)
        
        self.wifi_connection.currentIndexChanged.connect(self.connection_changed)
        self.wifi_encryption.currentIndexChanged.connect(self.encryption_changed)
        self.wifi_save.pressed.connect(self.save_pressed)
        self.wifi_show_status.pressed.connect(self.show_status_pressed)
        self.wifi_ca_certificate_browse.pressed.connect(self.ca_certificate_browse_pressed)
        self.wifi_client_certificate_browse.pressed.connect(self.client_certificate_browse_pressed)
        self.wifi_private_key_browse.pressed.connect(self.private_key_browse_pressed)
        
        self.connection_changed(0)
        self.encryption_changed(0)
        self.wifi_encryption.setCurrentIndex(encryption) # ensure that the correct encryption is displayed
        
    def get_wifi_configuration_async(self, configuration):
        ssid, connection, ip, sub, gw, port = configuration
        
        ssid = ssid.replace('\0', '')
        self.connection = connection
        
        self.wifi_ssid.setText(ssid);
        self.wifi_connection.setCurrentIndex(connection)
        self.wifi_ip1.setValue(ip[0])
        self.wifi_ip2.setValue(ip[1])
        self.wifi_ip3.setValue(ip[2])
        self.wifi_ip4.setValue(ip[3])
        self.wifi_sub1.setValue(sub[0])
        self.wifi_sub2.setValue(sub[1])
        self.wifi_sub3.setValue(sub[2])
        self.wifi_sub4.setValue(sub[3])
        self.wifi_gw1.setValue(gw[0])
        self.wifi_gw2.setValue(gw[1])
        self.wifi_gw3.setValue(gw[2])
        self.wifi_gw4.setValue(gw[3])
        self.wifi_port.setValue(port)
            
    def destroy(self):
        if self.wifi_status:
            self.wifi_status.close()

    def ca_certificate_browse_pressed(self):
        last_dir = ''
        if len(self.wifi_ca_certificate_url.text()) > 0:
            last_dir = os.path.dirname(os.path.realpath(unicode(self.wifi_ca_certificate_url.text().toUtf8(), 'utf-8')))

        file_name = QFileDialog.getOpenFileName(self,
                                                'Open CA Certificate',
                                                last_dir)
        if len(file_name) > 0:
            self.wifi_ca_certificate_url.setText(file_name)

    def client_certificate_browse_pressed(self):
        last_dir = ''
        if len(self.wifi_client_certificate_url.text()) > 0:
            last_dir = os.path.dirname(os.path.realpath(unicode(self.wifi_client_certificate_url.text().toUtf8(), 'utf-8')))

        file_name = QFileDialog.getOpenFileName(self,
                                                'Open Client Certificate',
                                                last_dir)
        if len(file_name) > 0:
            self.wifi_client_certificate_url.setText(file_name)

    def private_key_browse_pressed(self):
        last_dir = ''
        if len(self.wifi_private_key_url.text()) > 0:
            last_dir = os.path.dirname(os.path.realpath(unicode(self.wifi_private_key_url.text().toUtf8(), 'utf-8')))

        file_name = QFileDialog.getOpenFileName(self,
                                                'Open Private Key',
                                                last_dir)
        if len(file_name) > 0:
            self.wifi_private_key_url.setText(file_name)

    def encryption_changed(self, index):
        if str(self.wifi_encryption.currentText()) in 'WPA/WPA2':
            if self.parent.version >= (2, 0, 2):
                self.wifi_key.setMaxLength(63)
            else:
                self.wifi_key.setMaxLength(50)

            self.wifi_key.setVisible(True)
            self.wifi_key_label.setVisible(True)
            
            self.wifi_key_index.setVisible(False)
            self.wifi_key_index_label.setVisible(False)
            
            self.wifi_eap_inner_auth.setVisible(False)
            self.wifi_eap_inner_auth_label.setVisible(False)
            
            self.wifi_eap_outer_auth.setVisible(False)
            self.wifi_eap_outer_auth_label.setVisible(False)
            
            self.wifi_username.setVisible(False)
            self.wifi_username_label.setVisible(False)
            
            self.wifi_password.setVisible(False)
            self.wifi_password_label.setVisible(False)
            
            self.wifi_ca_certificate_url.setVisible(False)
            self.wifi_ca_certificate_browse.setVisible(False)
            self.wifi_ca_certificate_label.setVisible(False)
            self.wifi_client_certificate_url.setVisible(False)
            self.wifi_client_certificate_browse.setVisible(False)
            self.wifi_client_certificate_label.setVisible(False)
            self.wifi_private_key_url.setVisible(False)
            self.wifi_private_key_browse.setVisible(False)
            self.wifi_private_key_label.setVisible(False)
        elif str(self.wifi_encryption.currentText()) in 'WPA Enterprise':
            self.wifi_key.setVisible(False)
            self.wifi_key_label.setVisible(False)
            
            self.wifi_key_index.setVisible(False)
            self.wifi_key_index_label.setVisible(False)
            
            self.wifi_eap_inner_auth.setVisible(True)
            self.wifi_eap_inner_auth_label.setVisible(True)
            
            self.wifi_eap_outer_auth.setVisible(True)
            self.wifi_eap_outer_auth_label.setVisible(True)
                        
            self.wifi_username.setVisible(True)
            self.wifi_username_label.setVisible(True)
            
            self.wifi_password.setVisible(True)
            self.wifi_password_label.setVisible(True)
            
            self.wifi_ca_certificate_url.setVisible(True)
            self.wifi_ca_certificate_browse.setVisible(True)
            self.wifi_ca_certificate_label.setVisible(True)
            self.wifi_client_certificate_url.setVisible(True)
            self.wifi_client_certificate_browse.setVisible(True)
            self.wifi_client_certificate_label.setVisible(True)
            self.wifi_private_key_url.setVisible(True)
            self.wifi_private_key_browse.setVisible(True)
            self.wifi_private_key_label.setVisible(True)
        elif str(self.wifi_encryption.currentText()) in 'WEP':
            self.wifi_key.setMaxLength(26)
            self.wifi_key.setVisible(True)
            self.wifi_key_label.setVisible(True)
            
            self.wifi_key_index.setVisible(True)
            self.wifi_key_index_label.setVisible(True)
            
            self.wifi_eap_inner_auth.setVisible(False)
            self.wifi_eap_inner_auth_label.setVisible(False)
            
            self.wifi_eap_outer_auth.setVisible(False)
            self.wifi_eap_outer_auth_label.setVisible(False)
                        
            self.wifi_username.setVisible(False)
            self.wifi_username_label.setVisible(False)
            
            self.wifi_password.setVisible(False)
            self.wifi_password_label.setVisible(False)
            
            self.wifi_ca_certificate_url.setVisible(False)
            self.wifi_ca_certificate_browse.setVisible(False)
            self.wifi_ca_certificate_label.setVisible(False)
            self.wifi_client_certificate_url.setVisible(False)
            self.wifi_client_certificate_browse.setVisible(False)
            self.wifi_client_certificate_label.setVisible(False)
            self.wifi_private_key_url.setVisible(False)
            self.wifi_private_key_browse.setVisible(False)
            self.wifi_private_key_label.setVisible(False)
        else:
            self.wifi_key.setVisible(False)
            self.wifi_key_label.setVisible(False)
            
            self.wifi_key_index.setVisible(False)
            self.wifi_key_index_label.setVisible(False)
            
            self.wifi_eap_inner_auth.setVisible(False)
            self.wifi_eap_inner_auth_label.setVisible(False)
            
            self.wifi_eap_outer_auth.setVisible(False)
            self.wifi_eap_outer_auth_label.setVisible(False)
                        
            self.wifi_username.setVisible(False)
            self.wifi_username_label.setVisible(False)
            
            self.wifi_password.setVisible(False)
            self.wifi_password_label.setVisible(False)
            
            self.wifi_ca_certificate_url.setVisible(False)
            self.wifi_ca_certificate_browse.setVisible(False)
            self.wifi_ca_certificate_label.setVisible(False)
            self.wifi_client_certificate_url.setVisible(False)
            self.wifi_client_certificate_browse.setVisible(False)
            self.wifi_client_certificate_label.setVisible(False)
            self.wifi_private_key_url.setVisible(False)
            self.wifi_private_key_browse.setVisible(False)
            self.wifi_private_key_label.setVisible(False)
        
    def connection_changed(self, index):
        if self.wifi_connection.currentIndex() in (0, 2, 4):
            self.wifi_ip1.setVisible(False)
            self.wifi_ip2.setVisible(False)
            self.wifi_ip3.setVisible(False)
            self.wifi_ip4.setVisible(False)
            self.wifi_sub1.setVisible(False)
            self.wifi_sub2.setVisible(False)
            self.wifi_sub3.setVisible(False)
            self.wifi_sub4.setVisible(False)
            self.wifi_gw1.setVisible(False)
            self.wifi_gw2.setVisible(False)
            self.wifi_gw3.setVisible(False)
            self.wifi_gw4.setVisible(False)
            
            self.wifi_port.setVisible(True)
            self.wifi_port_label.setVisible(True)
            
            self.wifi_ip_label.setVisible(False)
            self.wifi_gw_label.setVisible(False)
            self.wifi_sub_label.setVisible(False)
            
            self.wifi_dot1.setVisible(False)
            self.wifi_dot2.setVisible(False)
            self.wifi_dot3.setVisible(False)
            self.wifi_dot4.setVisible(False)
            self.wifi_dot5.setVisible(False)
            self.wifi_dot6.setVisible(False)
            self.wifi_dot7.setVisible(False)
            self.wifi_dot8.setVisible(False)
            self.wifi_dot9.setVisible(False)
        else:
            self.wifi_ip1.setVisible(True)
            self.wifi_ip2.setVisible(True)
            self.wifi_ip3.setVisible(True)
            self.wifi_ip4.setVisible(True)
            self.wifi_sub1.setVisible(True)
            self.wifi_sub2.setVisible(True)
            self.wifi_sub3.setVisible(True)
            self.wifi_sub4.setVisible(True)
            self.wifi_gw1.setVisible(True)
            self.wifi_gw2.setVisible(True)
            self.wifi_gw3.setVisible(True)
            self.wifi_gw4.setVisible(True)
            
            self.wifi_port.setVisible(True)
            self.wifi_port_label.setVisible(True)
            
            self.wifi_ip_label.setVisible(True)
            self.wifi_gw_label.setVisible(True)
            self.wifi_sub_label.setVisible(True)
            
            self.wifi_dot1.setVisible(True)
            self.wifi_dot2.setVisible(True)
            self.wifi_dot3.setVisible(True)
            self.wifi_dot4.setVisible(True)
            self.wifi_dot5.setVisible(True)
            self.wifi_dot6.setVisible(True)
            self.wifi_dot7.setVisible(True)
            self.wifi_dot8.setVisible(True)
            self.wifi_dot9.setVisible(True)

        current = str(self.wifi_encryption.currentText())

        if self.wifi_connection.currentIndex() in (2, 3, 4, 5):
            self.wifi_encryption.clear()
            self.wifi_encryption.addItem('WEP')
            self.wifi_encryption.addItem('No Encryption')
        else:
            self.wifi_encryption.clear()
            self.wifi_encryption.addItem('WPA/WPA2')
            self.wifi_encryption.addItem('WPA Enterprise')
            self.wifi_encryption.addItem('WEP')
            self.wifi_encryption.addItem('No Encryption')

        index = self.wifi_encryption.findText(current)
        if index >= 0:
            self.wifi_encryption.setCurrentIndex(index)

    def popup_ok(self, message="Successfully saved configuration"):
        QMessageBox.information(self, "Configuration", message, QMessageBox.Ok)
    
    def popup_fail(self, message="Could not save configuration"):
        QMessageBox.critical(self, "Configuration", message, QMessageBox.Ok)

    def show_status_pressed(self):
        if self.wifi_status is None:
            self.wifi_status = WifiStatus(self)
            
        self.wifi_status.show()

    def create_progress_bar(self, title):
        progress = QProgressDialog(self)
        progress.setAutoClose(False)
        progress.setWindowTitle(title)
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModal)
        
        return progress
    
    def get_certificate(self, url_edit):
        cert_path = url_edit.text()
        cert_path = unicode(cert_path.toUtf8(), 'utf-8').encode(sys.getfilesystemencoding())
        try:
            if os.path.isfile(cert_path):
                certificate_file = map(ord, file(cert_path, 'rb').read()) # Convert certificate to list of bytes
                certificate_length = len(certificate_file)
                if certificate_length > 6*1024:
                    QMessageBox.critical(self, "Save", "Certificate too Big. Max size: 6kB.", QMessageBox.Ok)
                    return []
                
                return certificate_file
        except:
            return []

        return []
    
    def write_certificate(self, certificate, typ):
        try:
            chunks = []
            progress = self.create_progress_bar("Configuration")
            progress.setLabelText('Saving Certificate...')
            progress.setMaximum(1000)
            progress.setValue(0)
            progress.update()
            progress.show()
            
            position = 0
            length_certificate = len(certificate)
            while len(certificate) > 0:
                cert_chunk = certificate[:32]
                certificate = certificate[32:]
                length = len(cert_chunk)
                mod = length % 32
                if mod != 0:
                    cert_chunk += [0] * (32 - mod)
    
                time.sleep(0.01)
                self.master.set_wifi_certificate(10000*typ + position,
                                                 cert_chunk,
                                                 length)
                chunks.append(cert_chunk)
    
                position += 1
                progress.setValue(1000*position/(length_certificate/32))
                
            progress.setLabelText('Verifying Certificate...')
            progress.setValue(0)
            
            time.sleep(0.1)
    
            chunk_length = len(chunks)
            for i in range(chunk_length):
                old_chunk = list(self.master.get_wifi_certificate(10000*typ + i)[0])
                if old_chunk != chunks[i]:
                    progress.cancel()
                    return False
                progress.setValue(1000*i/chunk_length)
                
            progress.cancel()
        except:
            progress.cancel()
            return False

        return True

    def save_pressed(self):
        encryption = self.wifi_encryption.currentIndex()

        try:
            key = str(self.wifi_key.text()).decode('ascii')
        except:
            self.popup_fail('Key cannot contain non-ASCII characters')
            return

        if '"' in key:
            self.popup_fail('Key cannot contain quotation mark')
            return

        if str(self.wifi_encryption.currentText()) in 'WEP':
            if len(key) == 0:
                self.popup_fail('WEP key cannot be empty')
                return

            try:
                int(key, 16)
            except:
                self.popup_fail('WEP key has to be in hexadecimal notation')
                return

            if len(key) != 10 and len(key) != 26:
                self.popup_fail('WEP key has to be either 10 or 26 hexadecimal digits long')
                return

        long_key = key
        if str(self.wifi_encryption.currentText()) in 'WPA/WPA2':
            if len(key) < 8:
                self.popup_fail('WPA/WPA2 key has to be at least 8 chars long')
                return

            if self.parent.version >= (2, 0, 2) and len(key) > 50:
                key = '-'

        key_index = self.wifi_key_index.value()
        eap_outer = self.wifi_eap_outer_auth.currentIndex()
        eap_inner = self.wifi_eap_inner_auth.currentIndex()
            
        eap_options = eap_outer | (eap_inner << 2) 
        
        try:
            ssid = str(self.wifi_ssid.text()).decode('ascii')
        except:
            self.popup_fail('SSID cannot contain non-ASCII characters')
            return
        if len(ssid) == 0:
            self.popup_fail('SSID cannot be empty')
            return
        if '"' in ssid:
            self.popup_fail('SSID cannot contain quotation mark')
            return

        connection = self.wifi_connection.currentIndex()
        
        if connection in (2, 3, 4, 5):
            encryption += 2
        
        ip = (self.wifi_ip1.value(), self.wifi_ip2.value(),
              self.wifi_ip3.value(), self.wifi_ip4.value())
        sub = (self.wifi_sub1.value(), self.wifi_sub2.value(),
               self.wifi_sub3.value(), self.wifi_sub4.value())
        gw = (self.wifi_gw1.value(), self.wifi_gw2.value(),
              self.wifi_gw3.value(), self.wifi_gw4.value())
        port = self.wifi_port.value()
        
        power_mode = self.wifi_power_mode.currentIndex()
        ca_cert = self.get_certificate(self.wifi_ca_certificate_url)
        ca_certificate_length = len(ca_cert)
        client_cert = self.get_certificate(self.wifi_client_certificate_url)
        client_certificate_length = len(client_cert)
        priv_key = self.get_certificate(self.wifi_private_key_url)
        private_key_length = len(priv_key)

        previous_power_mode = self.master.get_wifi_power_mode()
        self.master.set_wifi_power_mode(power_mode)
        self.master.set_wifi_encryption(encryption, key, key_index, eap_options, ca_certificate_length, client_certificate_length, private_key_length)
        self.master.set_wifi_configuration(ssid, connection, ip, sub, gw, port)
        if self.parent.version >= (2, 0, 2):
            self.master.set_long_wifi_key(long_key)

        power_mode_old = self.master.get_wifi_power_mode()
        encryption_old, key_old, key_index_old, eap_options_old, ca_certificate_length_old, client_certificate_length_old, private_key_length_old = self.master.get_wifi_encryption()
        ssid_old, connection_old, ip_old, sub_old, gw_old, port_old = self.master.get_wifi_configuration()
        long_key_old = long_key
        if self.parent.version >= (2, 0, 2):
            long_key_old = self.master.get_long_wifi_key()

        test_ok = False
        
        if power_mode == power_mode_old and \
           encryption == encryption_old and key == key_old and \
           ssid == ssid_old and connection == connection_old and \
           ip == ip_old and sub == sub_old and gw == gw_old and \
           port == port_old and key_index == key_index_old and \
           eap_options == eap_options_old and \
           ca_certificate_length == ca_certificate_length_old and \
           client_certificate_length == client_certificate_length_old and \
           private_key_length == private_key_length_old and \
           long_key == long_key_old:
            test_ok = True
        
        if test_ok and encryption == 1:
            test_ok = False
            username = str(self.wifi_username.text())
            password = str(self.wifi_password.text())
            self.master.set_wifi_certificate(0xFFFF, map(ord, username) + [0] * (32 - len(username)), len(username))
            self.master.set_wifi_certificate(0xFFFE, map(ord, password) + [0] * (32 - len(password)), len(password))
            username_old = self.master.get_wifi_certificate(0xFFFF)
            username_old = ''.join(map(chr, username_old[0][:username_old[1]]))
            password_old = self.master.get_wifi_certificate(0xFFFE)
            password_old = ''.join(map(chr, password_old[0][:password_old[1]]))
            
            if username_old == username and password_old == password:
                test_ok = True

        if self.parent.version >= (1, 3, 4):
            if test_ok:
                self.master.set_wifi_regulatory_domain(self.wifi_domain.currentIndex())
                if self.master.get_wifi_regulatory_domain() != self.wifi_domain.currentIndex():
                    test_ok = False

        if test_ok:
            if len(ca_cert) > 0:
                test_ok = self.write_certificate(ca_cert, 0)
        if test_ok:
            if len(client_cert) > 0:
                test_ok = self.write_certificate(client_cert, 1)
        if test_ok:
            if len(priv_key) > 0:
                test_ok = self.write_certificate(priv_key, 2)

        if test_ok:
            if previous_power_mode != power_mode and power_mode == 1:
                self.popup_ok("Successfully saved configuration.\nPower Mode is not changed permanently, it will automatically switch back to Full Speed on reset.")
            else:
                self.popup_ok()
        else:
            self.popup_fail()

    def update_data(self):
        self.update_data_counter += 1
        if self.wifi_status != None:
            if self.wifi_status.isVisible():
                if self.update_data_counter % 100 == 0:
                    self.master.refresh_wifi_status()
                elif self.update_data_counter % 100 == 50:
                    self.wifi_status.update_status()
        
class Master(PluginBase, Ui_Master):
    def __init__(self, ipcon, uid, version):
        PluginBase.__init__(self, ipcon, uid, 'Master Brick', version)
        
        self.setupUi(self)

        self.master = BrickMaster(uid, ipcon)
        self.device = self.master
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)

        self.extension_type = None

        self.extensions = []
        self.num_extensions = 0

        self.extension_label.setText("None Present")
        
        # Chibi widget
        if self.version >= (1, 1, 0):
            self.extension_type_button.pressed.connect(self.extension_pressed)
            async_call(self.master.is_chibi_present, None, self.is_chibi_present_async, self.increase_error_count)
        else:
            self.extension_type_button.setEnabled(False)
            
        # RS485 widget
        if self.version >= (1, 2, 0):
            async_call(self.master.is_rs485_present, None, self.is_rs485_present_async, self.increase_error_count)
                
        # Wifi widget
        if self.version >= (1, 3, 0):
            async_call(self.master.is_wifi_present, None, self.is_wifi_present_async, self.increase_error_count)

    def is_wifi_present_async(self, present):
        if present:
            wifi = Wifi(self)
            self.extensions.append(wifi)
            self.extension_layout.addWidget(wifi)
            self.num_extensions += 1
            self.extension_label.setText("" + str(self.num_extensions) + " Present")
            
    def is_rs485_present_async(self, present):
        if present:
            rs485 = RS485(self)
            self.extensions.append(rs485)
            self.extension_layout.addWidget(rs485)
            self.num_extensions += 1
            self.extension_label.setText("" + str(self.num_extensions) + " Present")
            
    def is_chibi_present_async(self, present):
        if present:
            chibi = Chibi(self)
            self.extensions.append(chibi)
            self.extension_layout.addWidget(chibi)
            self.num_extensions += 1
            self.extension_label.setText("" + str(self.num_extensions) + " Present")

    def start(self):
        self.update_timer.start(100)

    def stop(self):
        self.update_timer.stop()

    def destroy(self):
        for extension in self.extensions:
            extension.destroy()

        if self.extension_type:
            self.extension_type.close()

    def has_reset_device(self):
        return self.version >= (1, 2, 1)

    def reset_device(self):
        if self.has_reset_device():
            self.master.reset()

    def is_brick(self):
        return True

    def is_hardware_version_relevant(self, hardware_version):
        return True

    def get_url_part(self):
        return 'master'

    @staticmethod
    def has_device_identifier(device_identifier):
        return device_identifier == BrickMaster.DEVICE_IDENTIFIER
    
    def update_data(self):
        async_call(self.master.get_stack_voltage, None, self.stack_voltage_update, self.increase_error_count)
        async_call(self.master.get_stack_current, None, self.stack_current_update, self.increase_error_count)
        
        for extension in self.extensions:
            extension.update_data()
        
    def stack_voltage_update(self, sv):
        sv_str = "%gV"  % round(sv/1000.0, 1)
        self.stack_voltage_label.setText(sv_str)
        
    def stack_current_update(self, sc):
        if sc < 999:
            sc_str = "%gmA" % sc
        else:
            sc_str = "%gA" % round(sc/1000.0, 1)   
        self.stack_current_label.setText(sc_str)
        
    def extension_pressed(self):
        if self.extension_type is None:
            self.extension_type = ExtensionTypeWindow(self)

        self.extension_type.show()
