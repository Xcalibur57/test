# -*- coding: utf-8 -*-
"""
Created on Mon Dec 09 10:33:00 2024

@author: mgoddard
"""

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QPoint
from datetime import datetime
from csv import writer
import numpy as np
import os
# import matplotlib.pyplot as plt
import pandas as pd

# import MISC.Misc_Functions as misc
import MISC.dialog_boxes as dialog

import MTF.MTF_Functions as MTF_Functions

def SelectInputDirectory(ui):
    dialog = QMessageBox()
    dialog.setWindowTitle("Take Note!")
    dialog.setText("Select a directory which contains folders of field positions and orientations.\n\n"
                    "Program will search for hard-coded positions, orientations and through focus range.")
    dialog.setWindowIcon(QIcon('_icons/MainWindow.png'))
    button = dialog.exec()
    
    if button == QMessageBox.Ok:
        print("OK")
    
    ui.TFinputdir_name = QFileDialog.getExistingDirectory(caption = "Select a Directory")
    ui.TFinputDirPath.setText(ui.TFinputdir_name)
    ui.GenerateCSVpushButton.setEnabled(True)
    
    # test(ui)

# def test(ui):
#     ui.topDataPlot_sag.plot_test()
#     # ui.top05DataPlot_sag.plot_test()
#     ui.centreDataPlot_sag.plot_test()
#     # ui.bot05DataPlot_sag.plot_test()
#     ui.botDataPlot_sag.plot_test()

#     ui.centreDataPlot_tan.plot_test()

#     ui.leftDataPlot_sag.plot_test()
#     # ui.left05DataPlot_sag.plot_test()
#     # ui.right05DataPlot_sag.plot_test()
#     ui.rightDataPlot_sag.plot_test()
#     pass

def GenerateEdgeCSV(ui):    
    if ui.TFinputdir_name != '':
    
        field_positions = ['top', 'top0.5', 'bottom', 'bottom0.5', 'centre', 'left', 'left0.5', 'right', 'right0.5']
        orientations = ['sagittal', 'tangential']
        focus_positions = ['+300', '+270', '+240', '+210', '+180', '+150', '+120', '+090', '+060', '+030', '-000', '-030', '-060', '-090', '-120']

        numfiles = 0
        for i in field_positions:
            for j in orientations:
                for k in focus_positions:
                    numfiles += 1
                    
        progress = QProgressDialog("Processing files...", "Cancel", 0, numfiles)
        progress.setWindowTitle('Please Wait')
        progress.setWindowIcon(QIcon('_icons/MainWindow.png'))
        progress.setWindowModality(Qt.WindowModal)

        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")

        with open(ui.TFinputdir_name + '/datalog_' + timestamp + '.csv', 'a', encoding='UTF8', newline='') as log:

            ui.logWriter = writer(log)

            header = ['FIELD', 'ORIENTATION', 'FOCUS',
                        '10-90 WIDTH', '20-80 WIDTH', 'XPOS', 'YPOS']

            ui.logWriter.writerow(header)
            
            filecounter = 0

            for ui.field in field_positions:
                if ui.field == 'top':
                    aoiPoint = QPoint(640, 50)
                elif ui.field == 'top0.5':
                    aoiPoint = QPoint(640, 281)
                elif ui.field == 'bottom0.5':
                    aoiPoint = QPoint(640, 743)
                elif ui.field == 'bottom':
                    aoiPoint = QPoint(640, 974)
                elif ui.field == 'centre':
                    aoiPoint = QPoint(640, 512)
                elif ui.field == 'left':
                    aoiPoint = QPoint(50, 512)
                elif ui.field == 'left0.5':
                    aoiPoint = QPoint(345, 512)
                elif ui.field == 'right0.5':
                    aoiPoint = QPoint(935, 512)
                elif ui.field == 'right':
                    aoiPoint = QPoint(1230, 512)

                for ui.orientation in orientations:
                    if ui.field == 'centre' and ui.orientation == 'sagittal':
                        ui.orientation = 'horizontal'
                    elif ui.field == 'centre' and ui.orientation == 'tangential':
                        ui.orientation = 'vertical'

                    ui.current_dir = ui.TFinputdir_name + '/' + ui.field + '_field_focussing_' + ui.orientation + 'edge'

                    for ui.focus in focus_positions:
                        filecounter += 1

                        ui.logRow = [ui.field,
                                        ui.orientation, ui.focus]
                        
                        image = 0
                        number_of_image_to_process = 2
                        for i in os.listdir(ui.current_dir):
                            if os.path.isfile(os.path.join(ui.current_dir, i)) and i.startswith(ui.focus):
                                image += 1
                                if image < number_of_image_to_process:
                                    pass
                                else:
                                    # print(os.path.join(ui.current_dir, i))
                                    MTF_Functions.loadImage(ui, os.path.join(ui.current_dir, i))
                                    MTF_Functions.setAoi(ui, aoiPoint, execute=True)
                                    MTF_Functions.findEdge(ui)
                                    MTF_Functions.analyse(ui, execute=True)
                                    break
                        ui.logRow.append(ui.aoiX.value())
                        ui.logRow.append(ui.aoiY.value())
                        ui.logWriter.writerow(ui.logRow)
                        
                        progress.setValue(filecounter)
                        
                        if progress.wasCanceled():
                            break
                    if progress.wasCanceled():
                        break
                if progress.wasCanceled():
                    dialog.messageWarning(ui, 'Warning!', 'Generating CSV file was cancelled - please load or generate a complete CSV before proceding.')
            if not progress.wasCanceled():
                dialog.messageInformation(ui, 'Complete', 'Generating CSV file is complete.')
                ui.TFinputDirPath_2.setText(ui.TFinputdir_name + '/datalog_' + timestamp + '.csv')

def ProcessEdgeCSV(ui):
    dialog = QMessageBox()
    dialog.setWindowTitle("Take Note!")
    dialog.setText("Select a .csv file which contains the output edge data.\n\n"
                    "Program will search for hard-coded positions, orientations, but will accept any through focus range.")
    dialog.setWindowIcon(QIcon('_icons/MainWindow.png'))
    button = dialog.exec()
    
    if button == QMessageBox.Ok:
        print("OK")
        
    fname = QFileDialog.getOpenFileName(caption = 'Open file', directory = '', initialFilter = 'Comma Separated Values (*.csv)')

    if fname[0] != '':
        data_frame = pd.read_csv(fname[0])
        
        top_sag = data_frame.loc[(data_frame["FIELD"] == 'top') & (data_frame["ORIENTATION"] == 'sagittal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        top_tan = data_frame.loc[(data_frame["FIELD"] == 'top') & (data_frame["ORIENTATION"] == 'tangential'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        top05_sag = data_frame.loc[(data_frame["FIELD"] == 'top0.5') & (data_frame["ORIENTATION"] == 'sagittal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        top05_tan = data_frame.loc[(data_frame["FIELD"] == 'top0.5') & (data_frame["ORIENTATION"] == 'tangential'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        bot_sag = data_frame.loc[(data_frame["FIELD"] == 'bottom') & (data_frame["ORIENTATION"] == 'sagittal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        bot_tan = data_frame.loc[(data_frame["FIELD"] == 'bottom') & (data_frame["ORIENTATION"] == 'tangential'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        bot05_sag = data_frame.loc[(data_frame["FIELD"] == 'bottom0.5') & (data_frame["ORIENTATION"] == 'sagittal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        bot05_tan = data_frame.loc[(data_frame["FIELD"] == 'bottom0.5') & (data_frame["ORIENTATION"] == 'tangential'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        centre_hor = data_frame.loc[(data_frame["FIELD"] == 'centre') & (data_frame["ORIENTATION"] == 'horizontal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        centre_ver = data_frame.loc[(data_frame["FIELD"] == 'centre') & (data_frame["ORIENTATION"] == 'vertical'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        left_sag = data_frame.loc[(data_frame["FIELD"] == 'left') & (data_frame["ORIENTATION"] == 'sagittal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        left_tan = data_frame.loc[(data_frame["FIELD"] == 'left') & (data_frame["ORIENTATION"] == 'tangential'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        left05_sag = data_frame.loc[(data_frame["FIELD"] == 'left0.5') & (data_frame["ORIENTATION"] == 'sagittal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        left05_tan = data_frame.loc[(data_frame["FIELD"] == 'left0.5') & (data_frame["ORIENTATION"] == 'tangential'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        right_sag = data_frame.loc[(data_frame["FIELD"] == 'right') & (data_frame["ORIENTATION"] == 'sagittal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        right_tan = data_frame.loc[(data_frame["FIELD"] == 'right') & (data_frame["ORIENTATION"] == 'tangential'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        right05_sag = data_frame.loc[(data_frame["FIELD"] == 'right0.5') & (data_frame["ORIENTATION"] == 'sagittal'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        right05_tan = data_frame.loc[(data_frame["FIELD"] == 'right0.5') & (data_frame["ORIENTATION"] == 'tangential'), ["FOCUS", "10-90 WIDTH", "20-80 WIDTH", "XPOS", "YPOS"]]
        
        top_sag_coeffs = np.polyfit(top_sag.loc[:,"FOCUS"].values, top_sag.loc[:,"20-80 WIDTH"], deg=2)
        top_tan_coeffs = np.polyfit(top_tan.loc[:,"FOCUS"].values, top_tan.loc[:,"20-80 WIDTH"], deg=2)
        top05_sag_coeffs = np.polyfit(top05_sag.loc[:,"FOCUS"].values, top05_sag.loc[:,"20-80 WIDTH"], deg=2)
        top05_tan_coeffs = np.polyfit(top05_tan.loc[:,"FOCUS"].values, top05_tan.loc[:,"20-80 WIDTH"], deg=2)
        bot_sag_coeffs = np.polyfit(bot_sag.loc[:,"FOCUS"].values, bot_sag.loc[:,"20-80 WIDTH"], deg=2)
        bot_tan_coeffs = np.polyfit(bot_tan.loc[:,"FOCUS"].values, bot_tan.loc[:,"20-80 WIDTH"], deg=2)
        bot05_sag_coeffs = np.polyfit(bot05_sag.loc[:,"FOCUS"].values, bot05_sag.loc[:,"20-80 WIDTH"], deg=2)
        bot05_tan_coeffs = np.polyfit(bot05_tan.loc[:,"FOCUS"].values, bot05_tan.loc[:,"20-80 WIDTH"], deg=2)
        centre_hor_coeffs = np.polyfit(centre_hor.loc[:,"FOCUS"].values, centre_hor.loc[:,"20-80 WIDTH"], deg=2)
        centre_ver_coeffs = np.polyfit(centre_ver.loc[:,"FOCUS"].values, centre_ver.loc[:,"20-80 WIDTH"], deg=2)
        left_sag_coeffs = np.polyfit(left_sag.loc[:,"FOCUS"].values, left_sag.loc[:,"20-80 WIDTH"], deg=2)
        left_tan_coeffs = np.polyfit(left_tan.loc[:,"FOCUS"].values, left_tan.loc[:,"20-80 WIDTH"], deg=2)
        left05_sag_coeffs = np.polyfit(left05_sag.loc[:,"FOCUS"].values, left05_sag.loc[:,"20-80 WIDTH"], deg=2)
        left05_tan_coeffs = np.polyfit(left05_tan.loc[:,"FOCUS"].values, left05_tan.loc[:,"20-80 WIDTH"], deg=2)
        right_sag_coeffs = np.polyfit(right_sag.loc[:,"FOCUS"].values, right_sag.loc[:,"20-80 WIDTH"], deg=2)
        right_tan_coeffs = np.polyfit(right_tan.loc[:,"FOCUS"].values, right_tan.loc[:,"20-80 WIDTH"], deg=2)
        right05_sag_coeffs = np.polyfit(right05_sag.loc[:,"FOCUS"].values, right05_sag.loc[:,"20-80 WIDTH"], deg=2)
        right05_tan_coeffs = np.polyfit(right05_tan.loc[:,"FOCUS"].values, right05_tan.loc[:,"20-80 WIDTH"], deg=2)

        ui.topDataPlot_sag.plot_through_focus('Top Saggital Through Focus', top_sag.loc[:,"FOCUS"].values, top_sag.loc[:,"20-80 WIDTH"], top_sag_coeffs)
        ui.top05DataPlot_sag.plot_through_focus('Top 0.5 Saggital Through Focus', top05_sag.loc[:,"FOCUS"].values, top05_sag.loc[:,"20-80 WIDTH"], top05_sag_coeffs)
        ui.botDataPlot_sag.plot_through_focus('Bottom Saggital Through Focus', bot_sag.loc[:,"FOCUS"].values, bot_sag.loc[:,"20-80 WIDTH"], bot_sag_coeffs)
        ui.bot05DataPlot_sag.plot_through_focus('Bottom 0.5 Saggital Through Focus', bot05_sag.loc[:,"FOCUS"].values, bot05_sag.loc[:,"20-80 WIDTH"], bot05_sag_coeffs)
        ui.leftDataPlot_sag.plot_through_focus('Left Saggital Through Focus', left_sag.loc[:,"FOCUS"].values, left_sag.loc[:,"20-80 WIDTH"], left_sag_coeffs)
        ui.left05DataPlot_sag.plot_through_focus('Left 0.5 Saggital Through Focus', left05_sag.loc[:,"FOCUS"].values, left05_sag.loc[:,"20-80 WIDTH"], left05_sag_coeffs)
        ui.rightDataPlot_sag.plot_through_focus('Right Saggital Through Focus', right_sag.loc[:,"FOCUS"].values, right_sag.loc[:,"20-80 WIDTH"], right_sag_coeffs)
        ui.right05DataPlot_sag.plot_through_focus('Right 0.5 Saggital Through Focus', right05_sag.loc[:,"FOCUS"].values, right05_sag.loc[:,"20-80 WIDTH"], right05_sag_coeffs)
        ui.centreDataPlot_sag.plot_through_focus('Centre Horizontal Through Focus', centre_hor.loc[:,"FOCUS"].values, centre_hor.loc[:,"20-80 WIDTH"], centre_hor_coeffs)

        ui.topDataPlot_tan.plot_through_focus('Top Tangential Through Focus', top_tan.loc[:,"FOCUS"].values, top_tan.loc[:,"20-80 WIDTH"], top_tan_coeffs)
        ui.top05DataPlot_tan.plot_through_focus('Top 0.5 Tangential Through Focus', top05_tan.loc[:,"FOCUS"].values, top05_tan.loc[:,"20-80 WIDTH"], top05_tan_coeffs)
        ui.botDataPlot_tan.plot_through_focus('Bottom Tangential Through Focus', bot_tan.loc[:,"FOCUS"].values, bot_tan.loc[:,"20-80 WIDTH"], bot_tan_coeffs)
        ui.bot05DataPlot_tan.plot_through_focus('Bottom 0.5 Tangential Through Focus', bot05_tan.loc[:,"FOCUS"].values, bot05_tan.loc[:,"20-80 WIDTH"], bot05_tan_coeffs)
        ui.leftDataPlot_tan.plot_through_focus('Left Tangential Through Focus', left_tan.loc[:,"FOCUS"].values, left_tan.loc[:,"20-80 WIDTH"], left_tan_coeffs)
        ui.left05DataPlot_tan.plot_through_focus('Left 0.5 Tangential Through Focus', left05_tan.loc[:,"FOCUS"].values, left05_tan.loc[:,"20-80 WIDTH"], left05_tan_coeffs)
        ui.rightDataPlot_tan.plot_through_focus('Right Tangential Through Focus', right_tan.loc[:,"FOCUS"].values, right_tan.loc[:,"20-80 WIDTH"], right_tan_coeffs)
        ui.right05DataPlot_tan.plot_through_focus('Right 0.5 Tangential Through Focus', right05_tan.loc[:,"FOCUS"].values, right05_tan.loc[:,"20-80 WIDTH"], right05_tan_coeffs)
        ui.centreDataPlot_tan.plot_through_focus('Centre Vertical Through Focus', centre_ver.loc[:,"FOCUS"].values, centre_ver.loc[:,"20-80 WIDTH"], centre_ver_coeffs)

        UpDownXsag = []
        UpDownFocussag = []
        LeftRightXsag = []
        LeftRightFocussag = []
        UpDownXtan = []
        UpDownFocustan = []
        LeftRightXtan = []
        LeftRightFocustan = []

        UpDownFocussag.append(float(np.roots(np.polyder(top_sag_coeffs))[0]))
        UpDownXsag.append(float(np.mean(top_sag.loc[:,"YPOS"].values)))
        UpDownFocussag.append(float(np.roots(np.polyder(top05_sag_coeffs))[0]))
        UpDownXsag.append(float(np.mean(top05_sag.loc[:,"YPOS"].values)))
        UpDownFocussag.append(float(np.roots(np.polyder(centre_ver_coeffs))[0]))
        UpDownXsag.append(float(np.mean(centre_ver.loc[:,"YPOS"].values)))
        UpDownFocussag.append(float(np.roots(np.polyder(bot05_sag_coeffs))[0]))
        UpDownXsag.append(float(np.mean(bot05_sag.loc[:,"YPOS"].values)))
        UpDownFocussag.append(float(np.roots(np.polyder(bot_sag_coeffs))[0]))
        UpDownXsag.append(float(np.mean(bot_sag.loc[:,"YPOS"].values)))

        UpDownFocustan.append(float(np.roots(np.polyder(top_tan_coeffs))[0]))
        UpDownXtan.append(float(np.mean(top_tan.loc[:,"YPOS"].values)))
        UpDownFocustan.append(float(np.roots(np.polyder(top05_tan_coeffs))[0]))
        UpDownXtan.append(float(np.mean(top05_tan.loc[:,"YPOS"].values)))
        UpDownFocustan.append(float(np.roots(np.polyder(centre_hor_coeffs))[0]))
        UpDownXtan.append(float(np.mean(centre_hor.loc[:,"YPOS"].values)))
        UpDownFocustan.append(float(np.roots(np.polyder(bot05_tan_coeffs))[0]))
        UpDownXtan.append(float(np.mean(bot05_tan.loc[:,"YPOS"].values)))
        UpDownFocustan.append(float(np.roots(np.polyder(bot_tan_coeffs))[0]))
        UpDownXtan.append(float(np.mean(bot_tan.loc[:,"YPOS"].values)))

        LeftRightFocussag.append(float(np.roots(np.polyder(left_sag_coeffs))[0]))
        LeftRightXsag.append(float(np.mean(left_sag.loc[:,"XPOS"].values)))
        LeftRightFocussag.append(float(np.roots(np.polyder(left05_sag_coeffs))[0]))
        LeftRightXsag.append(float(np.mean(left05_sag.loc[:,"XPOS"].values)))
        LeftRightFocussag.append(float(np.roots(np.polyder(centre_hor_coeffs))[0]))
        LeftRightXsag.append(float(np.mean(centre_hor.loc[:,"XPOS"].values)))
        LeftRightFocussag.append(float(np.roots(np.polyder(right05_sag_coeffs))[0]))
        LeftRightXsag.append(float(np.mean(right05_sag.loc[:,"XPOS"].values)))
        LeftRightFocussag.append(float(np.roots(np.polyder(right_sag_coeffs))[0]))
        LeftRightXsag.append(float(np.mean(right_sag.loc[:,"XPOS"].values)))

        LeftRightFocustan.append(float(np.roots(np.polyder(left_tan_coeffs))[0]))
        LeftRightXtan.append(float(np.mean(left_tan.loc[:,"XPOS"].values)))
        LeftRightFocustan.append(float(np.roots(np.polyder(left05_tan_coeffs))[0]))
        LeftRightXtan.append(float(np.mean(left05_tan.loc[:,"XPOS"].values)))
        LeftRightFocustan.append(float(np.roots(np.polyder(centre_ver_coeffs))[0]))
        LeftRightXtan.append(float(np.mean(centre_ver.loc[:,"XPOS"].values)))
        LeftRightFocustan.append(float(np.roots(np.polyder(right05_tan_coeffs))[0]))
        LeftRightXtan.append(float(np.mean(right05_tan.loc[:,"XPOS"].values)))
        LeftRightFocustan.append(float(np.roots(np.polyder(right_tan_coeffs))[0]))
        LeftRightXtan.append(float(np.mean(right_tan.loc[:,"XPOS"].values)))

        ui.upDownDataPlot.plot_tf_summary('Up Down Focus Performance', UpDownXsag, UpDownFocussag, UpDownXtan, UpDownFocustan)
        ui.leftRightDataPlot.plot_tf_summary('Left Right Focus Performance', LeftRightXsag, LeftRightFocussag, LeftRightXtan, LeftRightFocustan)

        # print(UpDownFocussag)
        # print(UpDownXsag)
        
        
        # plt.subplot(331)
        # plt.plot(top_sag.loc[:,"FOCUS"].values, top_sag.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(top_sag.loc[:,"FOCUS"].values, np.polyval(top_sag_coeffs, top_sag.loc[:,"FOCUS"].values), '--b', label = 'Sagittal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(top_sag_coeffs)):
        #     y = np.polyval(top_sag_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXsag.append(np.mean(top_sag.loc[:,"YPOS"].values))
        # UpDownFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Sagittal Best Focus')
        # plt.plot(top_tan.loc[:,"FOCUS"].values, top_tan.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(top_tan.loc[:,"FOCUS"].values, np.polyval(top_tan_coeffs, top_tan.loc[:,"FOCUS"].values), '--r', label = 'Tangential')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(top_tan_coeffs)):
        #     y = np.polyval(top_tan_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXtan.append(np.mean(top_tan.loc[:,"YPOS"].values))
        # UpDownFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Tangential Best Focus')
        # plt.title('Top')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.subplot(332)
        # plt.plot(top05_sag.loc[:,"FOCUS"].values, top05_sag.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(top05_sag.loc[:,"FOCUS"].values, misc.PolyCoefficients(top05_sag.loc[:,"FOCUS"].values, top05_sag_coeffs), '--b', label = 'Sagittal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(top05_sag_coeffs)):
        #     y = np.polyval(top05_sag_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXsag.append(np.mean(top05_sag.loc[:,"YPOS"].values))
        # UpDownFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Sagittal Best Focus')
        # plt.plot(top05_tan.loc[:,"FOCUS"].values, top05_tan.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(top05_tan.loc[:,"FOCUS"].values, misc.PolyCoefficients(top05_tan.loc[:,"FOCUS"].values, top05_tan_coeffs), '--r', label = 'Tangential')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(top05_tan_coeffs)):
        #     y = np.polyval(top05_tan_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXtan.append(np.mean(top05_tan.loc[:,"YPOS"].values))
        # UpDownFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Tangential Best Focus')
        # plt.title('Top 0.5')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.subplot(333)
        # plt.plot(bot_sag.loc[:,"FOCUS"].values, bot_sag.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(bot_sag.loc[:,"FOCUS"].values, misc.PolyCoefficients(bot_sag.loc[:,"FOCUS"].values, bot_sag_coeffs), '--b', label = 'Sagittal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(bot_sag_coeffs)):
        #     y = np.polyval(bot_sag_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXsag.append(np.mean(bot_sag.loc[:,"YPOS"].values))
        # UpDownFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Sagittal Best Focus')
        # plt.plot(bot_tan.loc[:,"FOCUS"].values, bot_tan.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(bot_tan.loc[:,"FOCUS"].values, misc.PolyCoefficients(bot_tan.loc[:,"FOCUS"].values, bot_tan_coeffs), '--r', label = 'Tangential')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(bot_tan_coeffs)):
        #     y = np.polyval(bot_tan_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXtan.append(np.mean(bot_tan.loc[:,"YPOS"].values))
        # UpDownFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Tangential Best Focus')
        # plt.title('Bottom')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.subplot(334)
        # plt.plot(bot05_sag.loc[:,"FOCUS"].values, bot05_sag.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(bot05_sag.loc[:,"FOCUS"].values, misc.PolyCoefficients(bot05_sag.loc[:,"FOCUS"].values, bot05_sag_coeffs), '--b', label = 'Sagittal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(bot05_sag_coeffs)):
        #     y = np.polyval(bot05_sag_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXsag.append(np.mean(bot05_sag.loc[:,"YPOS"].values))
        # UpDownFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Sagittal Best Focus')
        # plt.plot(bot05_tan.loc[:,"FOCUS"].values, bot05_tan.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(bot05_tan.loc[:,"FOCUS"].values, misc.PolyCoefficients(bot05_tan.loc[:,"FOCUS"].values, bot05_tan_coeffs), '--r', label = 'Tangential')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(bot05_tan_coeffs)):
        #     y = np.polyval(bot05_tan_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXtan.append(np.mean(bot05_tan.loc[:,"YPOS"].values))
        # UpDownFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Tangential Best Focus')
        # plt.title('Bottom 0.5')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.subplot(335)
        # plt.plot(centre_hor.loc[:,"FOCUS"].values, centre_hor.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(centre_hor.loc[:,"FOCUS"].values, misc.PolyCoefficients(centre_hor.loc[:,"FOCUS"].values, centre_hor_coeffs), '--b', label = 'Horizontal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(centre_hor_coeffs)):
        #     y = np.polyval(centre_hor_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXtan.append(np.mean(centre_hor.loc[:,"YPOS"].values))
        # UpDownFocustan.append(min_x)
        # LeftRightXsag.append(np.mean(centre_hor.loc[:,"XPOS"].values))
        # LeftRightFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Horizontal Best Focus')
        # plt.plot(centre_ver.loc[:,"FOCUS"].values, centre_ver.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(centre_ver.loc[:,"FOCUS"].values, misc.PolyCoefficients(centre_ver.loc[:,"FOCUS"].values, centre_ver_coeffs), '--r', label = 'Vertical')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(centre_ver_coeffs)):
        #     y = np.polyval(centre_ver_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # UpDownXsag.append(np.mean(centre_ver.loc[:,"YPOS"].values))
        # UpDownFocussag.append(min_x)
        # LeftRightXtan.append(np.mean(centre_ver.loc[:,"XPOS"].values))
        # LeftRightFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Vertical Best Focus')
        # plt.title('Centre')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.subplot(336)
        # plt.plot(left_sag.loc[:,"FOCUS"].values, left_sag.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(left_sag.loc[:,"FOCUS"].values, misc.PolyCoefficients(left_sag.loc[:,"FOCUS"].values, left_sag_coeffs), '--b', label = 'Sagittal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(left_sag_coeffs)):
        #     y = np.polyval(left_sag_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # LeftRightXsag.append(np.mean(left_sag.loc[:,"XPOS"].values))
        # LeftRightFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Sagittal Best Focus')
        # plt.plot(left_tan.loc[:,"FOCUS"].values, left_tan.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(left_tan.loc[:,"FOCUS"].values, misc.PolyCoefficients(left_tan.loc[:,"FOCUS"].values, left_tan_coeffs), '--r', label = 'Tangential')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(left_tan_coeffs)):
        #     y = np.polyval(left_tan_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # LeftRightXtan.append(np.mean(left_tan.loc[:,"XPOS"].values))
        # LeftRightFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Tangential Best Focus')
        # plt.title('Left')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.subplot(337)
        # plt.plot(left05_sag.loc[:,"FOCUS"].values, left05_sag.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(left05_sag.loc[:,"FOCUS"].values, misc.PolyCoefficients(left05_sag.loc[:,"FOCUS"].values, left05_sag_coeffs), '--b', label = 'Sagittal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(left05_sag_coeffs)):
        #     y = np.polyval(left05_sag_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # LeftRightXsag.append(np.mean(left05_sag.loc[:,"XPOS"].values))
        # LeftRightFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Sagittal Best Focus')
        # plt.plot(left05_tan.loc[:,"FOCUS"].values, left05_tan.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(left05_tan.loc[:,"FOCUS"].values, misc.PolyCoefficients(left05_tan.loc[:,"FOCUS"].values, left05_tan_coeffs), '--r', label = 'Tangential')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(left05_tan_coeffs)):
        #     y = np.polyval(left05_tan_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # LeftRightXtan.append(np.mean(left05_tan.loc[:,"XPOS"].values))
        # LeftRightFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Tangential Best Focus')
        # plt.title('Left 0.5')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.subplot(338)
        # plt.plot(right_sag.loc[:,"FOCUS"].values, right_sag.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(right_sag.loc[:,"FOCUS"].values, misc.PolyCoefficients(right_sag.loc[:,"FOCUS"].values, right_sag_coeffs), '--b', label = 'Sagittal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(right_sag_coeffs)):
        #     y = np.polyval(right_sag_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # LeftRightXsag.append(np.mean(right_sag.loc[:,"XPOS"].values))
        # LeftRightFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Sagittal Best Focus')
        # plt.plot(right_tan.loc[:,"FOCUS"].values, right_tan.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(right_tan.loc[:,"FOCUS"].values, misc.PolyCoefficients(right_tan.loc[:,"FOCUS"].values, right_tan_coeffs), '--r', label = 'Tangential')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(right_tan_coeffs)):
        #     y = np.polyval(right_tan_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # LeftRightXtan.append(np.mean(right_tan.loc[:,"XPOS"].values))
        # LeftRightFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Tangential Best Focus')
        # plt.title('Right')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.subplot(339)
        # plt.plot(right05_sag.loc[:,"FOCUS"].values, right05_sag.loc[:,"20-80 WIDTH"].values, 'ob')
        # plt.plot(right05_sag.loc[:,"FOCUS"].values, misc.PolyCoefficients(right05_sag.loc[:,"FOCUS"].values, right05_sag_coeffs), '--b', label = 'Sagittal')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(right05_sag_coeffs)):
        #     y = np.polyval(right05_sag_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # LeftRightXsag.append(np.mean(right05_sag.loc[:,"XPOS"].values))
        # LeftRightFocussag.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Sagittal Best Focus')
        # plt.plot(right05_tan.loc[:,"FOCUS"].values, right05_tan.loc[:,"20-80 WIDTH"].values, 'or')
        # plt.plot(right05_tan.loc[:,"FOCUS"].values, misc.PolyCoefficients(right05_tan.loc[:,"FOCUS"].values, right05_tan_coeffs), '--r', label = 'Tangential')
        # min_x = 0
        # min_y = 1000
        # for root in np.roots(np.polyder(right05_tan_coeffs)):
        #     y = np.polyval(right05_tan_coeffs, np.real(root))
        #     if y < min_y:
        #         min_x = np.real(root)
        #         min_y = y
        # LeftRightXtan.append(np.mean(right05_tan.loc[:,"XPOS"].values))
        # LeftRightFocustan.append(min_x)
        # plt.plot(min_x, min_y, 'o', label = 'Tangential Best Focus')
        # plt.title('Right 0.5')
        # plt.grid()
        # plt.xlabel('Focus Shift [um]')
        # plt.ylabel('Edge Width [px]')
        # plt.legend()
        
        # plt.tight_layout()
        # plt.show()
        
        
        # UpDownTanCoeffs = np.polyfit(UpDownXtan, UpDownFocustan, 2)
        # UpDownSagCoeffs = np.polyfit(UpDownXsag, UpDownFocussag, 2)
        # LeftRightTanCoeffs = np.polyfit(LeftRightXtan, LeftRightFocustan, 2)
        # LeftRightSagCoeffs = np.polyfit(LeftRightXsag, LeftRightFocussag, 2)
        # x_range = range(0, 1280)
        # y_range = range(0, 1024)
        
        # plt.figure(figsize=(12,12))
        
        # plt.subplot(211)
        # plt.plot(UpDownXtan, UpDownFocustan, 'or')
        # plt.plot(y_range, np.polyval(UpDownTanCoeffs, y_range), '--r', label = 'Tangential')
        # plt.plot(UpDownXsag, UpDownFocussag, 'ob')
        # plt.plot(y_range, np.polyval(UpDownSagCoeffs, y_range), '--b', label = 'Sagittal')
        # plt.grid()
        # plt.legend()
        # plt.title('Up-Down')
        # plt.ylim(40, 140)
        # plt.xlabel('Pixel Position [px]')
        # plt.ylabel('Focus Position [um]')
        
        # plt.subplot(212)
        # plt.plot(LeftRightXtan, LeftRightFocustan, 'or')
        # plt.plot(x_range, np.polyval(LeftRightTanCoeffs, x_range), '--r', label = 'Tangential')
        # plt.plot(LeftRightXsag, LeftRightFocussag, 'ob')
        # plt.plot(x_range, np.polyval(LeftRightSagCoeffs, x_range), '--b', label = 'Sagittal')
        # plt.grid()
        # plt.legend()
        # plt.ylim(40, 200)
        # plt.title('Left-Right')
        # plt.xlabel('Pixel Position [px]')
        # plt.ylabel('Focus Position [um]')
        
        # plt.tight_layout()
        # plt.show()