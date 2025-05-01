import sys

import numpy as np
import pywt
from openpyxl import load_workbook

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSizePolicy, QComboBox, QWidget, QLabel, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QWidget, QFileDialog, QMessageBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вейвлет фильтрация")
        self.setGeometry(100, 100, 800, 600)
        self.data = None
        self.filtered_data = None
        self.coeffs = None

        chbs_and_canvas_layout = QHBoxLayout()
        
        self.checkboxes = []
        checkbox_layout = QGridLayout()
        checkbox_layout.setSpacing(0)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)

        # selector
        self.selector = QComboBox()
        self.selector.addItems(["sym8", "sym20", "coif8", "coif17"])
        self.selector.move(0, 0)
        self.selector.currentIndexChanged.connect(self.total_update)
        self.selector.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.addWidget(self.selector, 0, 1)

        # checkboxes
        for i in range(5):
            cb = QCheckBox(f"Level {i+1}")
            cb.stateChanged.connect(self.calculate_and_plot)
            cb.setChecked(True)
            # cb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.checkboxes.append(cb)
            checkbox_layout.addWidget(cb, i + 1, 0)
        self.approx_checkbox = QCheckBox("Approximation")
        self.approx_checkbox.stateChanged.connect(self.calculate_and_plot)
        self.approx_checkbox.setChecked(True)
        checkbox_layout.addWidget(self.approx_checkbox, 6, 0)
        # to remove gaps
        for i in range(5):
            checkbox_layout.addWidget(QWidget())

        chbs_and_canvas_layout.addLayout(checkbox_layout)

        self.canvas = FigureCanvas(Figure(figsize=(20, 3)))
        self.ax = self.canvas.figure.add_subplot(111)

        chbs_and_canvas_layout.addWidget(self.canvas)

        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Загрузить CSV/TXT")
        self.load_button.clicked.connect(self.load_data)

        self.load_xlsx_button = QPushButton("Загрузить XLSX")
        self.load_xlsx_button.clicked.connect(self.load_xlsx_data)
        col_label = QLabel("Столбец")
        self.load_xlsx_col_input = QLineEdit("A")
        self.load_xlsx_skip_first = QCheckBox("Пропустить первое")
        self.load_xlsx_skip_first.setChecked(True)

        self.save_button = QPushButton("Сохранить вейвлет фильтрацию")
        self.save_button.clicked.connect(self.save_data)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.load_xlsx_button)
        button_layout.addWidget(col_label)
        button_layout.addWidget(self.load_xlsx_col_input)
        button_layout.addWidget(self.load_xlsx_skip_first)
        button_layout.addWidget(self.save_button)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addLayout(chbs_and_canvas_layout)
        layout.addWidget(self.load_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def total_update(self):
        self.generate_coeffs()
        self.calculate_and_plot()

    def generate_coeffs(self):
        if self.data is None:
            return
        
        wavelet = self.selector.currentText()
        level = 5

        self.coeffs = pywt.wavedec(self.data, wavelet=wavelet, level=level)
    
    def recover_coeffs(self):
        if self.coeffs is None:
            return
        
        wavelet = self.selector.currentText()
        level = 5

        cleared_coeffs = list()
        if self.approx_checkbox.isChecked():
            cleared_coeffs.append(self.coeffs[0])
        else:
            cleared_coeffs.append(np.zeros_like(self.coeffs[0]))
        
        for i in range(len(self.checkboxes)):
            if self.checkboxes[i].isChecked():
                cleared_coeffs.append(self.coeffs[i + 1])
            else:
                cleared_coeffs.append(np.zeros_like(self.coeffs[i + 1]))
        
        return np.array(pywt.waverec(cleared_coeffs, wavelet=wavelet), dtype='int32')

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "Текстовый файл (*.txt *.csv);;All Files (*)")
        if not file_path:
            return

        try:
            self.data = np.loadtxt(file_path, delimiter=None)
            self.total_update()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл\n{e}")

    def load_xlsx_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "Таблица (*.xlsx);;All Files (*)")
        if not file_path:
            return
        
        try:
            workbook = load_workbook(file_path, data_only=True)
            sheet = workbook.active

            column_data = []
            skipped = False
            for cell in sheet[self.load_xlsx_col_input.text()]:
                if self.load_xlsx_skip_first.isChecked() and not skipped:
                    skipped = True
                    continue

                if cell.value is not None:
                    column_data.append(cell.value)

            self.data = np.array(column_data)
            self.total_update()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл\n{e}")
            

    def save_data(self):
        if self.filtered_data is None:
            return
        
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить вейвлет фильтрацию")
        if not filepath:
            return
        
        try:
            np.savetxt(filepath, self.filtered_data, delimiter="\n", fmt="%i")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл\n{e}")

    def calculate_and_plot(self):
        if self.data is None:
            return
        
        self.filtered_data = self.recover_coeffs()
        
        self.ax.clear()
        self.ax.plot(self.data, color='tab:blue', label='Исходные данные')
        self.ax.plot(self.filtered_data, color='tab:orange', label='После фильтра')
        self.ax.set_title('Вейвлет фильтрация')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.legend()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec())
