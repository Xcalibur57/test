# -*- coding: utf-8 -*-
"""
Created on Sat Dec  3 14:25:05 2022

@author: mgoddard
"""
# import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout

# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches as mpatches

# from scipy.signal import savgol_filter

import numpy as np

# import random

class DataPlot(QWidget):
    def __init__(self, *args, **kwargs):
        super(DataPlot, self).__init__(*args, **kwargs)
        self.figure = plt.figure()
        
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        # layout.setSpacing(5)
        # layout.setMargin(0)
        layout.setContentsMargins(0,0,1,1)
        self.setLayout(layout)

    def plot_test(self):
        self.figure.clear()
        self.figure.tight_layout()
        
        ax = self.figure.add_subplot()

        ax.set_title('test', fontsize = 10)
        ax.set_xlabel('Pixels', fontsize = 10, labelpad = 5)
        ax.set_ylabel('Pixel Values', fontsize = 10, labelpad = 5)
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid()
        ax.plot([-200, -100, 0, 100], [5, 4, 3, 4], 'b*', label = 'Raw Data')
        ax.plot([-200, -100, 0, 100], [5.5, 4, 2.8, 4.5], 'r', label = 'Fit Data')
        ax.legend()
            
        self.setMinimumHeight(550)

    def plot_through_focus(self, title, positions, data, coeffs):

        root = np.roots(np.polyder(coeffs))[0]
        root_y = np.polyval(coeffs, root)
                 
        self.figure.clear()
        self.figure.tight_layout()
        
        ax = self.figure.add_subplot()

        ax.set_title(title, fontsize = 10)
        ax.set_xlabel('Focus Shift [um]', fontsize = 10, labelpad = 5)
        ax.set_ylabel('20%%-80%% Edge Width [px]', fontsize = 10, labelpad = 5)
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid()
        ax.plot(positions, data, 'b*', label = 'Raw Data')
        ax.plot(positions, np.polyval(coeffs, positions), '--r', label = 'Parabolic Fit')
        ax.plot(root, root_y, 'ko', label = 'Best Focus: {:.1f}'.format(root))
        ax.legend()
            
        self.setMinimumHeight(450)

    def plot_tf_summary(self, title, sag_positions, sag_values, tan_positions, tan_values):
        self.figure.clear()
        self.figure.tight_layout()

        sag_coeffs_1 = np.polyfit(sag_positions, sag_values, deg=1)
        sag_coeffs_2 = np.polyfit(sag_positions, sag_values, deg=2)
        tan_coeffs_1 = np.polyfit(tan_positions, tan_values, deg=1)
        tan_coeffs_2 = np.polyfit(tan_positions, tan_values, deg=2)
        
        ax = self.figure.add_subplot()

        ax.set_title(title, fontsize = 10)
        ax.set_xlabel('Detector Element Position [px]', fontsize = 10, labelpad = 5)
        ax.set_ylabel('Focus Position [um]', fontsize = 10, labelpad = 5)
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid()
        ax.plot(sag_positions, sag_values, linestyle = '', marker = '.', color = 'blue', label = 'Sag')
        ax.plot(tan_positions, tan_values, linestyle = '', marker = '.', color = 'orange', label = 'Tan')

        ax.plot(sag_positions, np.polyval(sag_coeffs_1, sag_positions), linestyle = 'dotted', marker = '', color = 'blue', label = 'Sag')
        ax.plot(tan_positions, np.polyval(tan_coeffs_1, tan_positions), linestyle = 'dotted', marker = '', color = 'orange', label = 'Tan')

        ax.plot(sag_positions, np.polyval(sag_coeffs_2, sag_positions), linestyle = 'solid', marker = '', color = 'blue', label = 'Sag')
        ax.plot(tan_positions, np.polyval(tan_coeffs_2, tan_positions), linestyle = 'solid', marker = '', color = 'orange', label = 'Tan')

        ax.legend()
            
        self.setMinimumHeight(450)
    
    def plotf(self, title, data, position, filtered_data = None, filtered_position = None, nyquist_range = None, detector_mtf = None, optical_mtf = None, tail_start = None, removed_data = None, removed_position = None):
        self.figure.clear()
        self.figure.tight_layout()
        
        ax = self.figure.add_subplot()
        
        if title == 'ESF':
            ax.set_title(title, fontsize = 14)
            ax.set_xlabel('Pixels', fontsize = 10, labelpad = 5)
            ax.set_ylabel('Pixel Values', fontsize = 10, labelpad = 5)
            ax.tick_params(axis='x', labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            # self.figure.tight_layout()
            ax.grid(True)
            ax.plot(position, data, 'b*', label = 'Raw Data')
            if removed_data is not None:
                ax.plot(removed_position, removed_data, 'r*', label = 'Removed Noise')
            
            if filtered_position is not None:
                ax.plot(filtered_position, filtered_data, 'r-', label = 'Best Fit')            
                
            ax.legend()
            
        if title == 'LSF':
            ax.set_title(title, fontsize = 14)
            ax.set_xlabel('Pixels', fontsize = 10, labelpad = 5)
            ax.set_ylabel('Derivative of Pixel Value', fontsize = 10, labelpad = 5)
            ax.tick_params(axis='x', labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            # self.figure.tight_layout()
            ax.grid(True)
            if abs(min(data)) > abs(max(data)):
                ax.plot(position, -data, 'b*')
                ax.plot(position, -data, 'r-')
            else:
                ax.plot(position, data, 'b*')
                ax.plot(position, data, 'r-')
        
        
        if title == 'MTF':
            halfNyquist = np.interp(32.5, position, data)
            ax.set_title(title, fontsize = 20)
            ax.set_xlabel('Spatial Frequency [lp/mm]', fontsize = 16, labelpad = 10)
            ax.set_xlim(0, nyquist_range)
            ax.set_ylabel('MTF', fontsize = 16, labelpad = 10)
            ax.set_ylim(0, 1.05)
            ax.tick_params(axis='x', labelsize=14)
            ax.tick_params(axis='y', labelsize=14)
            ax.grid(True)
            ax.plot(position, data, '-r', label = 'System MTF')       
            ax.plot(32.5, halfNyquist, 'ob', label = 'MTF @ Half-Nyquist = {:.3f}'.format(halfNyquist))
            # ax.plot(position, detector_mtf, '--m')
            halfNyquist = np.interp(32.5, position, optical_mtf)
            ax.plot(position, optical_mtf, '-b', label = 'Optical MTF')
            ax.plot(32.5, halfNyquist, 'og', label = 'Optical MTF @ Half-Nyquist = {:.3f}'.format(halfNyquist))
            ax.legend()
        
        self.canvas.draw()
        if title == 'MTF':
            self.setMinimumHeight(800)
        else:
            self.setMinimumHeight(550)