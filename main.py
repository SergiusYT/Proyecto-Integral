from PyQt5.QtWidgets import QApplication, QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from pid_controller import PID_Control
import sys
from collections import deque

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

class Form(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Proyecto Integral')
        self.initUi()

    def initUi(self):
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        gb1 = QGroupBox('Gráfico en Tiempo Real')
        gb2 = QGroupBox('Establecer Coeficientes')
        gb3 = QGroupBox('Descripción')

        vbox.addWidget(gb1)

        hbox = QHBoxLayout()
        hbox.addWidget(gb2)
        hbox.addWidget(gb3)
        hbox.setStretchFactor(gb2, 5)
        hbox.setStretchFactor(gb3, 5)
        vbox.addLayout(hbox)

        # GroupBox1
        vbox = QVBoxLayout()
        gb1.setLayout(vbox)

        self.fig = plt.Figure()
        self.canvas = FigureCanvasQTAgg(self.fig)
        vbox.addWidget(self.canvas)

        # GroupBox2
        gbox = QGridLayout()
        gb2.setLayout(gbox)

        _txt = ('Tiempo de Actualización (seg)', 'Mínimo', 'Máximo', 'Valor Objetivo', 'Proporcional (kp):', 'Integral (ki):', 'Derivativo (kd):')
        self.def_Coef = (0.1, -200., 200., 50., 0.1, 0.5, 0.01)
        self.coef = []
        self.lineEdits = []
        self.slds = []

        for i in range(len(_txt)):
            Lb = QLabel(_txt[i])
            Le = QLineEdit(str(self.def_Coef[i]))
            Le.setValidator(QDoubleValidator(-100, 100, 2))
            gbox.addWidget(Lb, i, 0)
            gbox.addWidget(Le, i, 1)
            self.lineEdits.append(Le)

        self.btn = QPushButton('Iniciar')
        self.btn.setCheckable(True)
        self.btnReset = QPushButton('Reiniciar')
        gbox.addWidget(self.btn, len(_txt)+1, 0)
        gbox.addWidget(self.btnReset, len(_txt)+1, 1)

        # GroupBox3
        vbox = QVBoxLayout()
        gb3.setLayout(vbox)
        self.desc = QLabel()
        vbox.addWidget(self.desc)

        # Señal
        self.btn.clicked.connect(self.onClickStart)
        self.btnReset.clicked.connect(self.onClickReset)

    def onClickStart(self):
        if self.btn.isChecked():
            self.btn.setText('Detener')
            self.enableCoefficient(False)
            if hasattr(self, 'ani'):
                self.resetAll()
                self.ani.event_source.start()
            else:
                self.startChart()
        else:
            self.btn.setText('Iniciar')
            self.enableCoefficient(True)
            self.ani.event_source.stop()

    def onClickReset(self):
        if hasattr(self, 'ani'):
            self.stopChart()
            self.fig.clear()
            self.canvas.draw()
            del(self.ani)
        self.btn.setChecked(False)
        self.btn.setText('Iniciar')
        self.enableCoefficient(True)

    def enableCoefficient(self, flag):
        for le in self.lineEdits:
            le.setEnabled(flag)

    def resetCoefficient(self, isDefault=False):
        self.coef.clear()
        # índice = 0: Tiempo de Actualización (t, seg), 1: Mínimo, 2: Máximo, 3: Valor Objetivo (sp), 4: Proporcional (kp), 5: Integral (ki), 6: Derivativo (kd)
        for i in range(len(self.def_Coef)):
            if isDefault:
                v = self.def_Coef[i]
                self.lineEdits[i].setText(str(v))
            else:
                v = float(self.lineEdits[i].text())
            self.coef.append(v)
        return self.coef

    def resetAll(self):
        # pid
        _dt, _min, _max, _sv, _kp, _ki, _kd = self.resetCoefficient(False)
        self.pid.update(_dt, _min, _max, _kp, _ki, _kd)
        # intervalo (ms)
        self.ani.event_source.interval = _dt*1000
        # escala
        self.ax.set_ylim(_min, _max)

    def startChart(self):
        self.resetCoefficient(False)
        _dt = self.coef[0] * 1000
        self.ani = animation.FuncAnimation(fig=self.fig, func=self.drawChart, init_func=self.initPlot, blit=False, interval=_dt)
        self.canvas.draw()

    def stopChart(self):
        self.ani._stop()

    def initPlot(self):
        _dt, _min, _max, _sv, _kp, _ki, _kd = self.resetCoefficient(True)

        self.pid = PID_Control(_dt, _min, _max, _kp, _ki, _kd)
        self.pv = _min
        self.inc = 0

        self.x = deque([], 100)
        self.y = deque([], 100)
        self.hy = deque([], 100)
        self.error_area = 0  # Inicializamos el área bajo la curva del error

        self.ax = self.fig.subplots()
        self.ax.set_title('Control PID')
        self.ax.set_ylim(_min, _max)
        self.line, = self.ax.plot(self.x, self.y, label='salida')
        self.spline, = self.ax.plot(self.x, self.hy, linestyle='--', label='punto de ajuste', color='r', alpha=0.7)
        self.area_patch = self.ax.fill_between(self.x, self.y, color='orange', alpha=0.3)  # Añadimos un relleno para el área bajo la curva del error
        self.ax.legend()
        return self.line, self.spline, self.area_patch

    def drawChart(self, i):
        inc, desc = self.pid.calc(self.coef[3], self.pv)
        self.desc.setText(desc)
        self.pv += inc
        self.y.append(self.pv)
        self.x.append(i)
        self.hy.append(self.coef[3])

        self.line.set_data(self.x, self.y)
        self.spline.set_data(self.x, self.hy)
        
        # Calculamos el área bajo la curva del error para el intervalo de tiempo actual
        if len(self.x) > 1:
            # Tomamos el último punto de datos
            x_end = self.x[-1]
            y_end = self.y[-1]
            
            # Tomamos el punto de datos anterior
            x_start = self.x[-2]
            y_start = self.y[-2]
            
            # Calculamos el área del rectángulo para este intervalo de tiempo
            rectangle_area = (x_end - x_start) * min(y_start, y_end)
            
            # Dibujamos el rectángulo
            rect = plt.Rectangle((x_start, 0), x_end - x_start, min(y_start, y_end), color='orange', alpha=0.3)
            self.ax.add_patch(rect)

        self.error_area += abs(inc) * self.coef[0]  # Acumulamos el área bajo la curva del error
        
        self.ax.relim()
        self.ax.autoscale_view(True, True, False)
        return self.line, self.spline
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Form()
    w.show()
    sys.exit(app.exec_())
