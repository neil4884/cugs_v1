# import sys as _sys
import numpy as _np
import matplotlib as _mpl
import threading as _threading
from typing import Union as _Union
from dataclasses import dataclass
from matplotlib import pyplot as _plt
from matplotlib import animation as _animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as _FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as _NavigationToolbar
from matplotlib.figure import Figure as _Figure
# from PySide6.QtWidgets import QMainWindow as _QMainWindow
# from PySide6.QtWidgets import QApplication as _QApplication
# from PySide6.QtWidgets import QVBoxLayout as _QVBoxLayout
# from PySide6.QtWidgets import QWidget as _QWidget

_mpl.use('QtAgg')
_plt.style.use('bmh')


# _plt.style.use('dark_background')


class MplDataClass:
    def __init__(self, use_np: bool = False):
        """
        MplDataClass (Upcoming)

        :param use_np:
        """
        self.use_np = use_np
        if self.use_np:
            self.x_data = _np.array([])
            self.y_data = _np.array([])
        else:
            self.x_data = []
            self.y_data = []

    def appendX(self, to_append):
        if(isinstance(self.x_data, _np.ndarray)):
            self.x_data = _np.append(self.x_data, to_append)
        else:
            self.x_data.append(to_append)
        return

    def appendY(self, *to_append):
        for i, __arr, __a in enumerate(zip(self.y_data, to_append)):
            if(isinstance(self.y_data, _np.ndarray)):
                self.y_data[i] = _np.append(__arr, __a)
            else:
                self.y_data[i].append(__a)
        return


class MplCanvasCli:
    def __init__(self, *labels, use_np: bool = False, reduce_func=None, interval: int = 500) -> None:
        """
        Matplotlib Animation Class

        :param labels:
        :param use_np:
        :param reduce_func:
        :param interval:
        """
        self.__label = labels
        self.__interval = interval
        self.__reduce_func = reduce_func
        self.__use_np = use_np
        self.__data_x = _np.array([])
        self.__data_y = [_np.array([])]
        self.__ani = _animation.FuncAnimation(_plt.gcf(), self.frontEndPlot, interval=self.__interval)
        _plt.tight_layout()
        _plt.show()

    def frontEndPlot(self, _i) -> None:
        _plt.cla()

        _data_x = self.__data_x
        _data_y = self.__data_y

        _new_data_x = self.__dummyReduceFunc(self.__reduce_func, _data_x)
        for indv_y, indv_lb in zip(_data_y, self.__label):
            _new_data_y = self.__dummyReduceFunc(self.__reduce_func, indv_y)
            _plt.plot(_new_data_x, _new_data_y, label=str(indv_lb))
        _plt.legend(loc='upper left')
        _plt.tight_layout()
        return

    def updatePlot(self, data_x: _Union[list, _np.ndarray], *data_y: _Union[list, _np.ndarray]):
        self.__data_x = data_x
        self.__data_y = data_y

    def forever(self, *args, **kwargs):
        return self.updatePlot(*args, **kwargs)

    @staticmethod
    def __dummyReduceFunc(_func, _dat):
        if _func is None:
            return _dat
        else:
            return _func(_dat)


class MplDataFetcher(_threading.Thread):
    """
    MplDataFetcher (Upcoming)

    """
    def __init__(self, DataClass=MplDataClass, interval=500):
        _threading.Thread.__init__(self)
        self.__data_class = DataClass
        self.__interval = interval / 1000

    def run(self):
        try:
            while True:
                pass
        except KeyboardInterrupt:
            pass



class MplCanvasQt(_FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100, use_np: bool = False, reduce_func=None) -> None:
        """
        Matplotlib class for PySide6 (Upcoming)

        :param parent: parent
        :param width: mpl width
        :param height: mpl height
        :param dpi: mpl dpi
        """
        self.__canvas_width = width
        self.__canvas_height = height
        self.__canvas_dpi = dpi
        self.__fig = _Figure(figsize=(self.__canvas_width, self.__canvas_height), dpi=self.__canvas_dpi)
        self.__axes = self.__fig.add_subplot(111)
        self.__reduce_func = reduce_func
        super(MplCanvasQt, self).__init__(self.__fig)

    def plotAll(self, data_x: _Union[list, _np.ndarray], data_y: _Union[list, _np.ndarray], mode: str = None):
        if mode:
            self.__axes.plot(data_x, data_y, mode)
        else:
            self.__axes.plot(data_x, data_y)

    def updatePlot(self, data_x: _Union[list, _np.ndarray], data_y: _Union[list, _np.ndarray]):
        self.clearCanvas()
        self.plotAll(data_x, data_y, 'r')
        self.__axes.draw()

    def clearCanvas(self):
        self.__axes.cla()


if __name__ == '__main__':
    mplcli = MplCanvasCli('xxx')
    mplcli.updatePlot(_np.array([1, 2, 3, 4, 5]), _np.array([3, 5, 8, 9, 1]))
