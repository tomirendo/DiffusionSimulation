#!/usr/local/bin/python3.5
import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QTableView,
    QTextEdit, QGridLayout, QApplication, QFileDialog, QPushButton, QMessageBox, QErrorMessage)
# from PyQt5.QtGui import QAbstractTableModel
from PyQt5.QtCore import Qt, pyqtSlot, QAbstractTableModel
from PyQt5 import QtCore
from simulation import Simulation


default_values = {   
    "total_time_in_seconds": 10, 
    "number_of_frames": 250, 
    "number_of_subframes_per_frame" : 100,


    "pixel_length_in_um": 0.117, 
    "z_direction_depth_in_um": 0.5, 

    "screen_size_in_pixels_x": 400, 
    "screen_size_in_pixels_y": 400,

    "sigma_x_noise_in_um" : 0.04,
    "sigma_y_noise_in_um" : 0.04,
    "background_noise_sigma" : 0.1
}

molecule_default_values = {
    "number_of_molecules": 5000, 
    "diffusion_coefficient_in_um^2_over_seconds": 0.5,
}

class MoleculeTableModel(QAbstractTableModel):
    def __init__(self, parent = None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.molecule_data = {k:[v] for k,v in molecule_default_values.items()}
        self.keys = list(molecule_default_values)
        self.types = {k:type(v) for k,v in molecule_default_values.items()}

    def rowCount(self, parent):
        return len(self.molecule_data[self.keys[0]])

    def columnCount(self, parent):
        return len(self.molecule_data)

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None

        return (self.molecule_data[self.keys[index.column()]][index.row()])
        # return self.molecule_data[self.keys[index.]]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        return self.keys[col].replace('_','').title()




types_dictionary = {k: type(v) for k,v in default_values.items()}

class Example(QWidget):
    
    def __init__(self):
        super().__init__()

        self.error_message = QErrorMessage(self)
        self.error_message.setWindowModality(Qt.WindowModal)

        self.gui_dictionary = {key:None for key in default_values}
        self.initUI()
        
    def initUI(self):

        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        for idx,(key, value) in enumerate(sorted(default_values.items())):
            text_label = key.replace('_',' ').title()
            value_str = str(value)
            label = QLabel(text_label)
            text_box = QLineEdit(value_str)
            text_box.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(label, idx+1, 0)
            self.grid.addWidget(text_box, idx+1, 1)
            self.gui_dictionary[key] = text_box

        self.create_video_button = QPushButton('Create Simulation')
        self.molecules_table_model = MoleculeTableModel()
        self.molecules_table = QTableView()
        self.molecules_table.setModel(self.molecules_table_model)

        self.create_video_button.clicked.connect(self.run_button_clicked)
        self.grid.addWidget(self.molecules_table, len(default_values) + 1, 0, 2, 3)
        self.grid.addWidget(self.create_video_button, len(default_values)+4, 0, 1, 2)


        self.setLayout(self.grid) 
        self.setGeometry(300, 300, 500, 300)
        self.setWindowTitle('Review')    
        self.show()

    @pyqtSlot()
    def run_button_clicked(self):
        setup_dictionary = {}
        for key, text_box in self.gui_dictionary.items():

            try: 
                setup_dictionary[key] = types_dictionary[key](text_box.text())

            except Exception as e:
                self.show_error("Problem parsing {}, \n {}".format(key, str(e)))
                return

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","",
                                                  "Tiff Files (*.tif)", 
                                                  options=options)
        if not filename:
            print(filename)

        simulation = Simulation(setup_dictionary)
        simulation.run()
        print("Done running")
        simulation.save_animation(filename)
        print("Done save_animationg")



    def show_error(self, message):
        self.error_message.showMessage(message)

    def set_enable_status(self, status):
        # for value in 
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
