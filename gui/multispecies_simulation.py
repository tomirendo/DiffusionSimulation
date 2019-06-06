import numpy as np
from itertools import chain
import json
from matplotlib import pyplot as plt
from scipy import optimize
from simulation import MOLECULES_KEY,maximum_value,frame_filename
import tifffile
import json
import os

class MultiSpeciesSimulation:
    def __init__(self, *subsimulations):
        self.subsimulations = subsimulations

        self._check_simulations()
        self._random_simulation = self.subsimulations[0]
        self.step_time_in_seconds = self._random_simulation.step_time_in_seconds


    def _check_simulations(self):
        if len(set([sim.step_time_in_seconds for sim in self.subsimulations])) != 1:
            raise Exception("All simulations need to have the same step_time_in_seconds")

    def run(self):
        for simulation in self.subsimulations:
            simulation.run()


    def to_dict(self):
        subdicts = [s.to_dict() for s in self.subsimulations]
        all_molecules = sum([d[MOLECULES_KEY] for d in subdicts],[])
        total_dict = dict(subdicts[0])
        total_dict[MOLECULES_KEY] = all_molecules
        return total_dict

    def to_json(self):
        return json.dumps(self.to_dict(), indent = 4)


    def create_frames(self):
        self.run()

        from ctypes import c_char_p, c_int, cdll
        lib = cdll.LoadLibrary("./Animation/animation.go.dll")
        # lib = cdll.LoadLibrary("./Animation/animation.go.so")
        lib.createAnimation.argtypes = [c_char_p]

        temp_file ="_temp_animation_file.json" 
        with open(temp_file ,"w") as f:
            f.write(self.to_json())
        lib.createAnimation(temp_file.encode())
        os.remove(temp_file)

    def save_frames_to_file(self, filename):
        # max_norm = maximum_value(range(self._random_simulation.number_of_frames))
        # MAX_INT16 = np.int16((2**15-1))
        # converter = np.int16(MAX_INT16 / max_norm)
        converter = np.int16(1)
        constant = np.int16(0)

        with tifffile.TiffWriter(filename, imagej = True) as stack:
            for idx in (range(self._random_simulation.number_of_frames)):
                image_filename = "{}.json".format(idx)
                with open(image_filename) as f:
                    frame = json.loads(f.read())
                os.remove(image_filename)
                stack.save(np.array(constant + self._random_simulation._add_noise_to_frame(frame) * converter,
                                 dtype = np.int16))

    def save_animation(self, filename):
        self.create_frames()
        self.save_frames_to_file(filename)
        