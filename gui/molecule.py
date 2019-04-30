import numpy as np
from matplotlib import pyplot as plt

POSITIONS_KEY = 'positions'
START_FRAME_KEY = 'start_frame'
INTENSITY_KEY = 'intensity'

class Molecule:
    def __init__(self, screen_size, 
                 pixel_length_in_um,
                 screen_depth_in_um,
                 diffusion_coefficient,
                 step_time_in_seconds,
                 number_of_frames,
                 intensity):
        
        #Save variables
        self.intensity = intensity
        self.screen_size = screen_size
        self.pixel_length_in_um = pixel_length_in_um
        self.screen_depth_in_um = screen_depth_in_um
        self.diffusion_coefficient = diffusion_coefficient
        self.step_time_in_seconds = step_time_in_seconds
        self.number_of_frames = number_of_frames

        self.step_size = np.sqrt(2 * self.diffusion_coefficient * self.step_time_in_seconds)
        self.screen_size_in_um = np.array([self.screen_size[0]*pixel_length_in_um, 
                                           self.screen_size[1]*pixel_length_in_um])

        self.start_frame = np.random.randint(0, self.number_of_frames)
        self.frame_count = self.start_frame
        
        #Randomize X,Y,Z
        self.x, self.y = np.random.uniform([0,0], 
                         self.screen_size_in_um)
        self.z = np.random.uniform(0, self.screen_depth_in_um)
        
        self.positions = [self.get_position()]


    def to_dict(self):
        d = {
            START_FRAME_KEY : self.start_frame,
            POSITIONS_KEY  : list(map(list,self.get_positions().T)),
            INTENSITY_KEY : self.intensity,
        }
        return d
    
    def _is_in_frame(self):
        x,y,z = self.x, self.y, self.z
        screen_size_x, screen_size_y = self.screen_size_in_um

        return (x > 0) & (x < screen_size_x) & (y > 0) & (y < screen_size_y) & (z >0) & (z < self.screen_depth_in_um)

    def _is_in_frame_filter(self):
        x, y, z = self.get_positions()
        screen_size_x, screen_size_y = self.screen_size_in_um

        return (x > 0) & (x < screen_size_x) & (y > 0) & (y < screen_size_y) & (z >0) & (z < self.screen_depth_in_um)

    def _max_n_for_mean_square_displacement(self):
        return self.get_length_of_journey() // 10

    def _square_displacement_vector(self, n):
        # Since we only measure 2D diffusion, we cannot measure the z displacement
        # We therefore ignore the Delta Z in the probability we measure.
        X, Y, Z = self.get_positions()

        x_tag = X[n:]
        y_tag = Y[n:]
        z_tag = Z[n:]

        X, Y, Z = X[:-n], Y[:-n], Z[:-n]

        return ((X - x_tag) ** 2 + (Y - y_tag) ** 2)

    def _mean_square_displacement_for_n(self, n):
        N = self.get_length_of_journey()

        normalization_factor = 1/(N-n)

        return normalization_factor * np.sum(self._square_displacement_vector(n))

    def get_position(self):
        return np.array([self.x, self.y, self.z])

    def get_position_in_frame(self, frame_number):

        if frame_number - self.start_frame < 0 :
            return None

        if len(self.positions)  <= frame_number - self.start_frame :
            return None

        return np.array(self.positions[frame_number - self.start_frame])

    def get_distance_of_journey(self, length = None):
        if length == None:
            length = self.get_length_of_journey()
        X0, Y0,_ = self.positions[0]
        Xn, Yn,_ = self.positions[length-1]
        return np.sqrt((X0-Xn)**2 + (Y0-Yn)**2)

    def get_positions(self, limit_to_frame = False):
        if limit_to_frame:
            _filter = self._is_in_frame_filter()
            return (np.array(self.positions)[_filter]).T
        return np.array(self.positions).T

    def get_length_of_journey(self):
        return len(self.positions)

    def get_mean_square_displacement(self, return_time_vector = True):
        """
            Calculates the mean square displacement vector of a molecule
            Returns a time series and a MSD series, for easy plotting
        """
        N = np.arange(1, self._max_n_for_mean_square_displacement())

        if return_time_vector:
            return [self.step_time_in_seconds * N,
                   [self._mean_square_displacement_for_n(n)  for 
                            n in N]]
        else :
            return [self._mean_square_displacement_for_n(n)  for 
                            n in N]


    def move(self, number_of_steps = 1, stop_when_out_of_frame = False):
        
        for _ in range(number_of_steps):

            # For movement in 3D
            # self.x, self.y, self.z = self.get_position() + np.random.normal(0, self.diffusion_coefficient,[3])

            self.x, self.y, self.z = self.get_position() + np.random.normal(0, self.step_size,[3])
            if stop_when_out_of_frame and not self._is_in_frame():
                self.x, self.y, self.z = self.positions[-1]
                return 
            self.positions.append(self.get_position())


    def plot(self, limit_to_frame = True):
        X,Y,Z = self.get_positions(limit_to_frame)
        return plt.plot(X, Y)

    def plot_mean_square_displacement(self, *args):
        x, y = self.get_mean_square_displacement()
        return plt.plot(x, y, *args)

        