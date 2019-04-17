#!/usr/local/bin/python3.5
import sys
import json
import threading
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QTableView, QTableWidget,QTableWidgetItem,QProgressBar,
    QTextEdit, QGridLayout, QApplication, QFileDialog, QPushButton, QMessageBox, QErrorMessage)
# from PyQt5.QtGui import QAbstractTableModel
from PyQt5.QtCore import Qt, pyqtSlot, QAbstractTableModel
from PyQt5 import QtCore
from simulation import Simulation
from multispecies_simulation import MultiSpeciesSimulation

MOLECULES_DICTIONARY_KEY = 'molecules'

COLUMN_CHAR_WIDTH = 7

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 600

ORIGINAL_POSITION_X = 100
ORIGINAL_POSITION_Y = 100

NUMBER_OF_ANIMATION_STEPS = 2
STATUS_LABEL_INITAL_VALUE = 'Click `Create Simulation` to begin'

treads = []
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

class MoleculeTableModel():
    def __init__(self, parent = None, *args):
        self.molecule_data = {k:[v] for k,v in molecule_default_values.items()}
        self.keys = sorted(list(molecule_default_values))
        self.types = {k:type(v) for k,v in molecule_default_values.items()}
        self.table_widget = QTableWidget()
        self.init_table()

    def init_table(self):
        self.table_widget.setRowCount(self.row_count())
        self.table_widget.setColumnCount(self.column_count())
        for i, key in enumerate(self.keys):
            for j, value in enumerate(self.molecule_data[key]):
                self.table_widget.setItem(j, i, QTableWidgetItem(str(value)))
            self.table_widget.setColumnWidth(i, len(key) * COLUMN_CHAR_WIDTH)

        self.table_widget.setHorizontalHeaderLabels([k.replace('_',' ').title() 
                                                for k in self.keys])

    def data_to_array(self, data):
        return list([data[k] for k in self.keys])

    def array_to_data(self, array):
        return {k:list(v) for k,v in zip(self.keys, array)}

    def table_to_array(self):
        res = []
        for i, key in enumerate(self.keys):
            res.append([self.table_widget.item(j, i).text() for j in range(self.row_count())])
        return res


    def row_count(self):
        return len(self.molecule_data[self.keys[0]])

    def column_count(self):
        return len(self.molecule_data)

    def update_data(self):
        self.molecule_data = self.array_to_data(self.table_to_array())

    def add_row(self):
        self.update_data()
        for key in self.keys:
            self.molecule_data[key].append(molecule_default_values[key])
        self.init_table()

    def get_molecules(self, gui_object):
        """
            Returns a list of dictionaries for each molecule
        """
        res = []
        for idx in range(self.row_count()): 
            try: 
                molecule_dictionary = {}
                for key in self.keys:
                    molecule_dictionary[key] = self.types[key](self.molecule_data[key][idx])
                res.append(molecule_dictionary)
            except Exception as e:
                gui_object.show_error("Problem parsing {}, \n {}".format(key, str(e)))
                return
        return res


    # def headerData(self, col, orientation, role):
    #     if orientation == Qt.Horizontal:
    #         return (self.keys[col].replace('_',' ').title()) #     return None




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
        self.add_molecule_type = QPushButton('Add Molecule')

        self.molecules_table_model = MoleculeTableModel()
        self.molecules_table = self.molecules_table_model.table_widget

        self.create_video_button.clicked.connect(self.run_button_clicked)
        self.add_molecule_type.clicked.connect(self.add_molecule)

        self.grid.addWidget(self.add_molecule_type, len(default_values) + 1, 0, 2, 1)
        self.grid.addWidget(self.molecules_table, len(default_values) + 1, 1, 2, 1)
        self.grid.addWidget(self.create_video_button, len(default_values)+3, 0, 1, 2)


        self.progress_bar = QProgressBar()
        self.status_label = QLabel(STATUS_LABEL_INITAL_VALUE)
        self.grid.addWidget(self.progress_bar, len(default_values)+4,1,1,1)
        self.grid.addWidget(self.status_label, len(default_values)+4,0,1,1)

        self.setLayout(self.grid) 
        self.setGeometry(ORIGINAL_POSITION_X, ORIGINAL_POSITION_Y, 
                          WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowTitle('Molecule Magic Mixer')    
        self.show()

    @pyqtSlot()
    def add_molecule(self):
        self.molecules_table_model.add_row()

    @pyqtSlot()
    def run_button_clicked(self):
        self.set_enable_status(False)
        self.molecules_table_model.update_data()

        molecules_dictionaries = self.molecules_table_model.get_molecules(self)
        if molecules_dictionaries is None:
            """
                An Error Occurred
            """
            return

        setup_dictionary = self.create_setup_dictionary()
        if setup_dictionary is None:
            return


        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","",
                                                  "Tiff Files (*.tif)", 
                                                  options=options)

        if not filename:
            return 

        self.init_progress_bar(len(molecules_dictionaries))

        def worker():
            self.set_status_label("Running Simulations")
            simulations = []
            for index, molecule_dict in enumerate(molecules_dictionaries):
                simulation_dictionary = dict(setup_dictionary)
                simulation_dictionary.update(molecule_dict)
                simulation = Simulation(simulation_dictionary)
                simulation.run()
                simulations.append(simulation)
                self.progress_bar.setValue(index)

            multispecies_simulation = MultiSpeciesSimulation(*simulations)

            self.progress_bar.setValue(self.progress_bar.value() + 1)
            self.set_status_label("Creating Frames")
            multispecies_simulation.create_frames()

            self.progress_bar.setValue(self.progress_bar.value() + 1)
            self.set_status_label("Saving to file")
            multispecies_simulation.save_frames_to_file(filename)
            self.save_setup(setup_dictionary, molecules_dictionaries, filename)

            self.progress_bar.setValue(self.progress_bar.value() + 1)
            self.set_status_label("Done!")
            self.set_enable_status(True)

        t = threading.Thread(target = worker)
        treads.append(t)
        t.start()


    def show_error(self, message):
        self.error_message.showMessage(message)
        self.set_enable_status(True)

    def set_enable_status(self, status):
        # for value in 
        for widget in self.gui_dictionary.values():
            widget.setEnabled(status)
        self.molecules_table_model.table_widget.setEnabled(status)
        self.create_video_button.setEnabled(status)
        self.add_molecule_type.setEnabled(status)

    def init_progress_bar(self, number_of_molecules):
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimum(0) 
        self.progress_bar.setMaximum(number_of_molecules + NUMBER_OF_ANIMATION_STEPS)

    def set_status_label(self, text):
        self.status_label.setText(text)

    def create_setup_dictionary(self):
        setup_dictionary = {}
        for key, text_box in self.gui_dictionary.items():
            try: 
                setup_dictionary[key] = types_dictionary[key](text_box.text())

            except Exception as e:
                self.show_error("Problem parsing {}, \n {}".format(key, str(e)))
                return
        return setup_dictionary

    def create_simulation_dictionary(self, setup_dictionary, molecules_dictionaries):
        d = dict(setup_dictionary)
        d[MOLECULES_DICTIONARY_KEY] = molecules_dictionaries
        return d

    def save_setup(self, setup_dictionary, molecules_dictionaries, filename):
        with open(filename + ".json", "w") as f:
            f.write(json.dumps(setup_dictionary))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
