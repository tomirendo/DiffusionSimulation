#CONSTANTS

PIXEL_LENGTH_IN_UM_KEY = 'pixel_length_in_um'
NUMBER_OF_FRAMES_KEY = 'number_of_frames'
NUMBER_OF_MOLECULES_KEY = 'number_of_molecules'
SCREEN_SIZE_IN_PIXELS_X_KEY = 'screen_size_in_pixels_x'
SCREEN_SIZE_IN_PIXELS_Y_KEY = 'screen_size_in_pixels_y'
DIFFUSION_COEFFICIENT_KEY = 'diffusion_coefficient_in_um^2_over_seconds'
TOTAL_TIME_IN_SECONDS_KEY = 'total_time_in_seconds'
Z_DIRECTION_DEPTH_IN_UM_KEY = 'z_direction_depth_in_um'
NUMBER_OF_FRAMES_KEY = 'number_of_frames'
EXPOSURE_TIME_IN_MS_KEY = 'exposure_time_in_ms'
NUMBER_OF_SUBFRAMES_PER_FRAME_KEY = 'number_of_subframes_per_frame'
STEP_TIME_IN_SECONDS_KEY = 'step_time_in_seconds'
PSF_SIGMA_IN_UM_X_AXIS  = 'psf_sigma_in_um_x_axis'
PSF_SIGMA_IN_UM_Y_AXIS  = 'psf_sigma_in_um_y_axis'
BACKGROUND_NOISE_AMPLITUDE_KEY = 'background_noise_amplitude'
INTENSITY_KEY = 'intensity'
SECONDS_IN_MS = 1e-3

MOLECULES_KEY = 'molecules'

from molecule import *
from scipy.special import erf
from numpy import sqrt
from matplotlib import pyplot as plt
import numpy as np
from tqdm import tqdm_notebook as tqdm
from IPython import display
from matplotlib.animation import FuncAnimation, ArtistAnimation
# from skimage.external import tifffile
import tifffile
import json
import os

def frame_filename(idx):
    return "{}.json".format(idx)

def maximum_value(index_range):
    filenames = [frame_filename(idx) for idx in index_range]
    maximum = 0 
    for filename in filenames:
        with open(filename) as f:
            maximum = np.max([np.max(json.loads(f.read())), maximum])
    return maximum

class Simulation:
    def __init__(self, parameters):
        self.parameters =  parameters
        self.intensity = parameters[INTENSITY_KEY]
        self.pixel_length_in_um = parameters[PIXEL_LENGTH_IN_UM_KEY]
        self.number_of_molecules = parameters[NUMBER_OF_MOLECULES_KEY]
        self.screen_size = [parameters[SCREEN_SIZE_IN_PIXELS_X_KEY],
                            parameters[SCREEN_SIZE_IN_PIXELS_Y_KEY]]
        self.z_direction_depth_in_um = parameters[Z_DIRECTION_DEPTH_IN_UM_KEY]
        self.diffusion_coefficient = parameters[DIFFUSION_COEFFICIENT_KEY]
        self.total_time_in_seconds = parameters[TOTAL_TIME_IN_SECONDS_KEY]
        self.exposure_time_in_seconds = parameters[EXPOSURE_TIME_IN_MS_KEY] * SECONDS_IN_MS
        self.number_of_frames = int(round(self.total_time_in_seconds / self.exposure_time_in_seconds)) #parameters[NUMBER_OF_FRAMES_KEY]
        self.sigma_x_noise_in_um = parameters[PSF_SIGMA_IN_UM_X_AXIS]
        self.sigma_y_noise_in_um = parameters[PSF_SIGMA_IN_UM_Y_AXIS]
        self.number_of_subframes_per_frame = parameters[NUMBER_OF_SUBFRAMES_PER_FRAME_KEY]
        self.background_noise_amplitude = parameters[BACKGROUND_NOISE_AMPLITUDE_KEY]
        
        self.number_of_steps = self.number_of_frames * self.number_of_subframes_per_frame
        self.step_time_in_seconds = self.total_time_in_seconds / self.number_of_steps 
        self.frame_time_in_seconds = self.total_time_in_seconds / self.number_of_frames

        self.step_size = np.sqrt(2 * self.diffusion_coefficient * self.step_time_in_seconds)

        
        self.molecules = [Molecule(self.screen_size, 
                                   self.pixel_length_in_um,
                                   self.z_direction_depth_in_um,
                                   self.diffusion_coefficient,
                                   self.step_time_in_seconds,
                                   self.number_of_steps,
                                   self.intensity) 
                          for _ in range(self.number_of_molecules)]
        self.did_run = False
    def to_dict(self):
        d = {
            PIXEL_LENGTH_IN_UM_KEY : self.pixel_length_in_um,
            NUMBER_OF_FRAMES_KEY : self.number_of_frames,
            BACKGROUND_NOISE_AMPLITUDE_KEY : self.background_noise_amplitude,
            NUMBER_OF_SUBFRAMES_PER_FRAME_KEY : self.number_of_subframes_per_frame,
            SCREEN_SIZE_IN_PIXELS_X_KEY : self.screen_size[0],
            SCREEN_SIZE_IN_PIXELS_Y_KEY : self.screen_size[1],
            PSF_SIGMA_IN_UM_X_AXIS : self.sigma_x_noise_in_um,
            PSF_SIGMA_IN_UM_Y_AXIS : self.sigma_y_noise_in_um,
            MOLECULES_KEY : [m.to_dict() for m in self.molecules]
        }
        return d

    def to_json(self):
        return json.dumps(self.to_dict(), indent = 4)

    def write_to_file(self, filename):
        with open(filename,"w") as f:
            f.write(self.to_json())

    def _get_positions_in_frame(self,n):
        positions = []
        for m in self.molecules:
            pos = m.get_position_in_frame(n)
            if pos is not None:
                positions.append(pos)
        return positions

    def _create_frame(self, n, verbose = False):
        x_axis= np.arange(self.screen_size[0]) * self.pixel_length_in_um
        y_axis = np.arange(self.screen_size[1]) * self.pixel_length_in_um

        x_mesh, y_mesh = np.meshgrid(x_axis, y_axis)

        frame = 0 * x_mesh

        if verbose:
            _tqdm = tqdm
        else :
            _tqdm = lambda x : x

        for subframe in range(self.number_of_subframes_per_frame):
            molecule_subframe = n*self.number_of_subframes_per_frame+subframe
            for position in _tqdm(self._get_positions_in_frame(molecule_subframe)):
                x,y,_ = position
                frame += self.PSF(x_mesh, y_mesh, x, y)

        return frame

    def PSF(self, x_mesh, y_mesh, x0, y0):
        x,y = x_mesh, y_mesh
        # # sigma_x = sqrt(2) * self.sigma_x_noise_in_um
        # # sigma_y = sqrt(2) * self.sigma_y_noise_in_um
        # return (erf(x-x0+.5) - erf(x-x0-.5))* (erf(y - y0 +.5) - erf(y - y0 - .5))/(sigma_x * sigma_y)

        return 1/(2*np.pi*self.sigma_y_noise_in_um*self.sigma_x_noise_in_um)*np.exp(- (x-x0)**2/(2*self.sigma_x_noise_in_um**2))*np.exp(-(y-y0)**2/(2*self.sigma_y_noise_in_um**2))

    def plot_frame(self, n, verbose = True):
        return plt.imshow(self._create_frame(n, verbose = verbose), cmap = 'Greys_r')

    def _add_noise_to_frame(self, frame):
        frame = np.array(frame)
        return frame + np.random.exponential(self.background_noise_amplitude, self.screen_size)
                    # np.abs(np.random.normal(0, self.background_noise_sigma * np.sqrt(self.number_of_subframes_per_frame), self.screen_size))

    def save_animation(self, filename, verbose = False):
        self.run()
        if verbose:
            _tqdm = tqdm
        else :
            _tqdm = lambda x:x

        from ctypes import c_char_p, c_int, cdll
        # lib = cdll.LoadLibrary("./Animation/animation.go.so")
        lib = cdll.LoadLibrary("./Animation/animation.go.dll")
        lib.createAnimation.argtypes = [c_char_p]


        temp_file ="_temp_animation_file.json" 
        with open(temp_file ,"w") as f:
            f.write(self.to_json())
        lib.createAnimation(temp_file.encode())
        os.remove(temp_file)

        max_norm = maximum_value(range(self.number_of_frames))
        MAX_INT16 = np.int16((2**15-1))
        converter = np.int16(MAX_INT16 / max_norm)
        constant = np.int16(0)

        with tifffile.TiffWriter(filename, imagej = True) as stack:
            for idx in _tqdm(range(self.number_of_frames)):
                image_filename = "{}.json".format(idx)
                with open(image_filename) as f:
                    frame = json.loads(f.read())
                os.remove(image_filename)
                stack.save(np.array(constant + self._add_noise_to_frame(frame) * converter,
                                 dtype = np.int16))


    def get_animation(self):
        self.run()
        from ctypes import c_char_p, c_int, cdll
        # lib = cdll.LoadLibrary("./Animation/animation.go.so")
        lib = cdll.LoadLibrary("./Animation/animation.go.dll")
        lib.createAnimation.argtypes = [c_char_p]

        temp_file ="_temp_animation_file.json" 
        with open(temp_file ,"w") as f:
            f.write(self.to_json())
        lib.createAnimation(temp_file.encode())
        os.remove(temp_file)

        fig = plt.figure()

        max_norm = np.mean([self.sigma_y_noise_in_um, self.sigma_x_noise_in_um])/self.step_size 
        norm =  plt.Normalize(0, max_norm * np.sqrt(self.number_of_subframes_per_frame))

        # with tifffile.TiffWriter(filename) as stack:
        #     for idx in tqdm(range(1, self.number_of_frames)):
        #         with open("/tmp/{}.json".format(idx)) as f:
        #             frame = json.loads(f.read())
        #         # im = plt.imshow(frame, animated = True, 
        #         #                 cmap = 'Greys_r', norm = norm)
        #         stack.save(np.array(frame, dtype = np.float64))


        with open("0.json") as f:
            frame = json.loads(f.read())
        im = plt.imshow(frame, animated = True, 
                cmap = 'Greys_r', norm = norm)

        def updatefig(idx):
            frame_filename = frame_filename(idx)
            with open(frame_filename) as f:
                frame = json.loads(f.read())
            os.remove(image_filename)
            im.set_array(self._add_noise_to_frame(frame))
            return im,

        ani = FuncAnimation(fig, updatefig,
                                interval=self.frame_time_in_seconds*1e3, 
                                frames = tqdm(range(1,self.number_of_frames)),
                                blit=True)


        return ani

    def plot_animation(self):
        return display.HTML(self.get_animation().to_html5_video())
    

    def _get_diffusion_coefficient_slopes(self):
        vectors = [m._square_displacement_vector(1) for m in self.molecules
                                if m.get_length_of_journey() > 1]
        slopes = np.concatenate(vectors)
        return slopes 

    def run(self, stop_when_out_of_frame = True, verbose = True):
        if self.did_run:
            return

        if verbose:
            _tqdm = tqdm
        else:
            _tqdm = lambda x:x
            
        for molecule in _tqdm(self.molecules):
            molecule.move(self.number_of_steps, 
                          stop_when_out_of_frame = stop_when_out_of_frame)
        self.did_run = True

    def get_journies_by_length(self, length = 2):
        return [m for m in self.molecules if m.get_length_of_journey() >= length]

    def get_length_of_journies(self):
        return [m.get_length_of_journey() for m in self.molecules]

    def approximate_diffusion_ceofficient(self, number_of_dimensions_of_diffusion = 2, verbose = True):
        slopes = self._get_diffusion_coefficient_slopes()
        approximation = np.mean(slopes) / number_of_dimensions_of_diffusion / self.step_time_in_seconds /2
        print("Approximation : {}\nValue : {}\nRatio : {}".format(approximation, self.diffusion_coefficient, approximation/self.diffusion_coefficient))
        return approximation

    def plot_mean_square_displacement_curves(self, *args):
        for m in tqdm(self.molecules):
            m.plot_mean_square_displacement(*args)

    def plot_length_of_journies(self, *args):
        return plt.hist(self.get_length_of_journies(), *args)

        
        
        