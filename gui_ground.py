import sys
import lib as ilib
import gui as guilib
# import numpy as np
from lib import Log
# from typing import Union as _Union
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor


class ProgFullStackGUI:
    def __init__(self, pref_dict: dict) -> None:
        # Back end Initialization
        self.exit_code = 0
        self.data_format = pref_dict['data_format'] if 'data_format' in pref_dict else []
        self.header = pref_dict['header'] if 'header' in pref_dict else ''
        self.save_name = pref_dict['file_name'] if pref_dict['file_name'] else 'test_file'
        self.extension = pref_dict['file_ext'] if pref_dict['file_ext'] else 'csv'
        self.main_ui_file = pref_dict['main_ui'] if pref_dict['main_ui'] else 'gui/cugs_mainwindow.ui'
        self.plot_engine = pref_dict['plot_engine'] if pref_dict['plot_engine'] else 'qchart'
        self.to_plot_y = pref_dict['use_plot']['y']
        self.to_plot_x = pref_dict['use_plot']['x']

        # Plot_X Broadcasting
        if isinstance(self.to_plot_x, str):
            self.to_plot_x = [self.to_plot_x] * len(self.to_plot_y)
        else:
            if 0 < len(self.to_plot_x) < len(self.to_plot_y):
                self.to_plot_x += [self.to_plot_x[-1]] * (len(self.to_plot_y) - len(self.to_plot_x))

        self.logger = Log(target='GUI_STACK')

        # Objects Initialization
        self.ui_main = guilib.GuiLoader(self.main_ui_file).ui
        self.ui_csv = guilib.GuiLoader('gui/cugs_csv_liveview.ui').ui
        self.parser = ilib.Parser(self.data_format, header=self.header)
        self.directory = ilib.LoadDirectory(__file__, self.save_name, self.extension)
        self.com = ilib.ComPort()
        self.mpl_widgets = [
            self.ui_main.mpl_c1,
            self.ui_main.mpl_c2,
            self.ui_main.mpl_c3,
            self.ui_main.mpl_c4,
            self.ui_main.mpl_c5,
            self.ui_main.mpl_c6,
            self.ui_main.mpl_c7,
            self.ui_main.mpl_c8,
            self.ui_main.mpl_c9
        ]
        self.mpl_title = [
            self.ui_main.lb_main1,
            self.ui_main.lb_main2,
            self.ui_main.lb_sub1,
            self.ui_main.lb_sub2,
            self.ui_main.lb_sub3,
            self.ui_main.lb_sub4,
            self.ui_main.lb_sub5,
            self.ui_main.lb_sub6,
            self.ui_main.lb_sub7,
        ]
        if self.plot_engine == 'qchart':
            __plot_engine = ilib.QChartData
        else:
            __plot_engine = ilib.PyQtGraphData
        self.mpl_charts = [
            __plot_engine(mpl_w) for mpl_w in self.mpl_widgets
        ]

        self.plot_list = [
            [c, x, y]
            for c, x, y in zip(self.mpl_charts,
                               self.to_plot_x[:len(self.mpl_charts)],
                               self.to_plot_y[:len(self.mpl_charts)])
        ]

        self.table_main = ilib.QTableData(self.ui_main.table_kv_payload)
        self.table_csv = ilib.QTableData(self.ui_csv.table_csv)

        # Variables Initialization
        self.com_baudrate = 0
        self.com_portname = ''
        self.timer_thread = None
        self.serial_logger = None
        self.serial_connected = False
        self.serial_thread = None
        self.serial_plain_text = ''
        self.serial_parsed_dict = dict()
        self.start_mission_stat = False
        self.pause_data = False
        self.dict_data_array = self.parser.createBlankDataDict()

        # Front end Initialization
        self.setupUi()
        self.connectButons()
        self.updateButtonsLogic()
        self.setSerialDropDown()

        # Other
        pass

    def setupUi(self) -> None:
        # Text
        self.ui_main.setWindowTitle("CU Ground Station V1")
        self.ui_main.combo_serial.clear()
        self.ui_main.text_serial_mon.clear()
        self.ui_main.text_serial_info.clear()
        self.ui_main.text_sys_log.clear()

        # Table
        self.ui_main.table_kv_payload.setRowCount(len(self.data_format))
        for r, k in enumerate(self.data_format):
            self.ui_main.table_kv_payload.setItem(r, 0, QTableWidgetItem(k))

        # Charts
        for mpl_t, c_name in zip(self.mpl_title, self.to_plot_y):
            mpl_t.setText(c_name)

        return

    def start(self) -> None:
        self.ui_main.show()
        return

    def stop(self) -> int:
        self.com.disconnect()
        return self.exit_code

    def connectButons(self) -> None:
        self.ui_main.btn_serial_connect.clicked.connect(self.serialConnect)
        self.ui_main.btn_serial_disconnect.clicked.connect(self.serialDisconnect)
        self.ui_main.btn_serial_refresh.clicked.connect(self.listRefreshSerial)

        self.ui_main.btn_start_mission.clicked.connect(self.updateButtonsLogic)
        self.ui_main.btn_start_pause_data.clicked.connect(self.updateButtonsLogic)
        self.ui_main.btn_csv_live.clicked.connect(self.startCsvLiveView)

        self.ui_main.btn_chart_pop.clicked.connect(self.popPlot)
        self.ui_main.btn_chart_clear.clicked.connect(self.clearPlot)

        self.ui_csv.btn_clear.clicked.connect(lambda: self.table_csv.clear())
        self.ui_csv.btn_pop.clicked.connect(lambda: self.table_csv.pop())
        return

    def setSerialDropDown(self) -> None:
        self.ui_main.combo_serial.clear()
        self.com.refreshPortList()
        self.ui_main.combo_serial.addItems(self.com.port_dict)
        return

    def setupThreadSerial(self) -> None:
        self.serial_thread = ilib.ThreadSerial(serial_logger=self.serial_logger)
        self.serial_thread.msg_carrier.connect(self.updateBackEnds)
        return

    def setupThreadTimer(self) -> None:
        return

    def listRefreshSerial(self) -> None:
        self.setSerialDropDown()
        return

    def serialConnect(self) -> None:
        self.com_baudrate = int(self.ui_main.combo_baud.currentText())
        self.com_portname = self.ui_main.combo_serial.currentText()
        if self.com.connect(self.com_portname, self.com_baudrate):
            self.ui_main.tabWidget_Cmd.setCurrentWidget(self.ui_main.tab_data)
            self.serial_connected = True
            self.serial_logger = ilib.LogSerial(self.com.device, header=self.header)
            self.setupThreadSerial()
            self.serial_thread.start()
        return

    def serialDisconnect(self) -> None:
        try:
            if self.serial_connected:
                self.serial_thread.stop()
            if self.com.disconnect():
                self.serial_connected = False
        except Exception:
            return
        return

    def startMission(self) -> None:
        return

    def startCsvLiveView(self) -> None:
        self.ui_csv.setWindowTitle("CU Ground Station V1 - CSV Tabular Liveview")
        self.ui_csv.show()
        return

    def updateButtonsLogic(self) -> None:
        self.start_mission_stat = self.ui_main.btn_start_mission.isChecked()
        self.pause_data = self.ui_main.btn_start_pause_data.isChecked()
        return

    def updateBackEnds(self, serial_text_in) -> None:
        # Raw Data Processing
        self.serial_plain_text = serial_text_in
        self.serial_parsed_dict = self.parser.parseData(serial_text_in)
        # self.parser.append(self.dict_data_array, self.serial_parsed_dict)
        try:
            __coord = ilib.Coordinate(
                latitude=self.serial_parsed_dict['gps_lat'],
                longitude=self.serial_parsed_dict['gps_lon'],
                altitude=self.serial_parsed_dict['bar_alt']
            )
        except KeyError:
            __coord = ilib.Coordinate(
                latitude=None,
                longitude=None,
                altitude=None
            )

        # Serial Monitor
        self.ui_main.text_serial_mon.appendPlainText(self.serial_plain_text)
        self.ui_main.text_serial_mon.moveCursor(QTextCursor.End)

        # File Appending
        self.directory.appendEarthCoord(__coord)
        self.directory.appendDelimitedFile(self.directory.dictToList(self.serial_parsed_dict, self.data_format),
                                           self.serial_plain_text)

        # Key-Value Table
        self.table_main.replaceVector(self.serial_parsed_dict)

        # CSV Liveview Table
        self.table_csv.appendTable(self.serial_parsed_dict)

        # Update plot data
        self.updatePlot()

        # Update Exit code
        self.exit_code += 1
        return

    def updatePlot(self) -> None:
        __to_plot_data = []
        for __chart, __key_x, __key_y in self.plot_list:
            if __key_y not in self.serial_parsed_dict:
                continue
            if __key_x not in self.serial_parsed_dict:
                continue
            if type(self.serial_parsed_dict[__key_y]) not in [int, float]:
                continue
            if type(self.serial_parsed_dict[__key_x]) not in [int, float]:
                continue
            __data_y = self.serial_parsed_dict[__key_y]
            __chart.append(float(self.serial_parsed_dict[__key_x]), __data_y)
            __chart.setTitle(__data_y, __key_y)
        return

    def clearPlot(self):
        for __chart, _, _ in self.plot_list:
            __chart.clear()

    def popPlot(self):
        for __chart, _, _ in self.plot_list:
            __chart.pop()


def run_prog(pref_file_name: str = 'cugs_preferences.json'):
    log = Log(target='GUI_PROG')
    log.info('Start of Program')
    prog_preferences = ilib.PreferencesData('lib/' + pref_file_name).getPreferences()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)

    prog = ProgFullStackGUI(prog_preferences)
    prog.start()

    app.exec()
    prog.stop()
    log.info('Program exited with code ' + str(prog.exit_code))

    return prog.exit_code


if __name__ == '__main__':
    run_prog()
