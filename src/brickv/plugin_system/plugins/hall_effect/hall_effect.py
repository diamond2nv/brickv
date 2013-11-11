# -*- coding: utf-8 -*-  
"""
Hall Effect Plugin
Copyright (C) 2013 Olaf Lüke <olaf@tinkerforge.com>

hall_effect.py: Hall Effect Plugin Implementation

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

from brickv.plugin_system.plugin_base import PluginBase
from brickv.bindings.bricklet_hall_effect import BrickletHallEffect
from brickv.async_call import async_call
from brickv.plot_widget import PlotWidget
from brickv.plugin_system.plugins.hall_effect.ui_hall_effect import Ui_HallEffect

from PyQt4.QtGui import QVBoxLayout, QHBoxLayout
from PyQt4.QtCore import pyqtSignal, Qt
import PyQt4.Qwt5 as Qwt
    
class HallEffect(PluginBase, Ui_HallEffect):
    qtcb_edge_count = pyqtSignal(int, bool)
    
    def __init__(self, ipcon, uid, version):
        PluginBase.__init__(self, ipcon, uid, 'Hall Effect Bricklet', version)
        
        self.setupUi(self)

        self.hf = BrickletHallEffect(uid, ipcon)
        
        self.qtcb_edge_count.connect(self.cb_edge_count)
        self.hf.register_callback(self.hf.CALLBACK_EDGE_COUNT,
                                  self.qtcb_edge_count.emit) 
        
        self.current_value = None

        plot_list = [['', Qt.red, self.get_current_value]]
        axis_scales = [(Qwt.QwtPlot.yLeft, 0, 1, 1)]
        self.plot_widget = PlotWidget('Value', plot_list, axis_scales=axis_scales)

        self.combo_edge_type.activated.connect(self.edge_changed)
        self.spin_debounce.editingFinished.connect(self.debounce_changed)
        
        self.main_layout.insertWidget(1, self.plot_widget)
        
    def debounce_changed(self):
        self.hf.set_edge_count_config(self.combo_edge_type.currentIndex(), self.spin_debounce.value())
        
    def edge_changed(self, value):
        self.hf.set_edge_count_config(self.combo_edge_type.currentIndex(), self.spin_debounce.value())
        
    def cb_edge_count(self, count, value):
        self.label_edge_count.setText(str(count))
        if value:
            self.current_value = 1
        else:
            self.current_value = 0
    
    def get_current_value(self):
        return self.current_value

    def cb_edge_count_config(self, conf):
        edge_type, debounce = conf
        self.combo_edge_type.setCurrentIndex(edge_type)
        self.spin_debounce.setValue(debounce)

    def start(self):
        async_call(self.hf.get_edge_count_config, None, self.cb_edge_count_config, self.increase_error_count)
        async_call(self.hf.set_edge_count_callback_period, 50, None, self.increase_error_count)
        
        self.plot_widget.stop = False
        
    def stop(self):
        async_call(self.hf.set_edge_count_callback_period, 0, None, self.increase_error_count)
        
        self.plot_widget.stop = True

    def get_url_part(self):
        return 'hall_effect'

    @staticmethod
    def has_device_identifier(device_identifier):
        return device_identifier == BrickletHallEffect.DEVICE_IDENTIFIER