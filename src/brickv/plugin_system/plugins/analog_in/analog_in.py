# -*- coding: utf-8 -*-  
"""
Analog In Plugin
Copyright (C) 2011-2012 Olaf Lüke <olaf@tinkerforge.com>

analog_in.py: Analog In Plugin Implementation

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
from plot_widget import PlotWidget
from bindings import ip_connection
from bindings.bricklet_analog_in import BrickletAnalogIn
from async_call import async_call

from PyQt4.QtGui import QVBoxLayout, QLabel, QHBoxLayout
from PyQt4.QtCore import pyqtSignal, Qt
        
class VoltageLabel(QLabel):
    def setText(self, text):
        text = "Voltage: " + text + " V"
        super(VoltageLabel, self).setText(text)
    
class AnalogIn(PluginBase):
    qtcb_voltage = pyqtSignal(int)
    
    def __init__(self, ipcon, uid, version):
        PluginBase.__init__(self, ipcon, uid, 'Analog In Bricklet', version)
        
        self.ai = BrickletAnalogIn(uid, ipcon)
        
        self.qtcb_voltage.connect(self.cb_voltage)
        self.ai.register_callback(self.ai.CALLBACK_VOLTAGE,
                                  self.qtcb_voltage.emit) 
        
        self.voltage_label = VoltageLabel('Voltage: ')
        
        self.current_value = 0
        
        plot_list = [['', Qt.red, self.get_current_value]]
        self.plot_widget = PlotWidget('Voltage [mV]', plot_list)
        
        layout_h = QHBoxLayout()
        layout_h.addStretch()
        layout_h.addWidget(self.voltage_label)
        layout_h.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(layout_h)
        layout.addWidget(self.plot_widget)
        
    def start(self):
        async_call(self.ai.get_voltage, None, self.cb_voltage, self.increase_error_count)
        async_call(self.ai.set_voltage_callback_period, 100, None, self.increase_error_count)
        
        self.plot_widget.stop = False
        
    def stop(self):
        async_call(self.ai.set_voltage_callback_period, 0, None, self.increase_error_count)
        
        self.plot_widget.stop = True

    def get_url_part(self):
        return 'analog_in'

    @staticmethod
    def has_device_identifier(device_identifier):
        return device_identifier == BrickletAnalogIn.DEVICE_IDENTIFIER

    def get_current_value(self):
        return self.current_value

    def cb_voltage(self, voltage):
        self.current_value = voltage
        self.voltage_label.setText(str(voltage/1000.0))
