import numpy as np
from itertools import chain
from matplotlib import pyplot as plt
from scipy import optimize

class TwoSpeciesSimulation:
    def __init__(self, *subsimulations):
        self.subsimulations = subsimulations

        self._check_simulations()
        self.step_time_in_seconds = self.subsimulations[0].step_time_in_seconds

        for simulation in self.subsimulations:
            simulation.run()


    def _check_simulations(self):
        if len(set([sim.step_time_in_seconds for sim in self.subsimulations])) != 1:
            raise Exception("All simulations need to have the same step_time_in_seconds")


    def get_molecules_with_journey_length(self, n = 2,
                                          return_as_simulation = False):
        return [[m for m in simulation.molecules if m.get_length_of_journey() >= n]
                 for simulation in self.subsimulations]

    def get_distance_of_journies(self, length = 2):
        if length < 2:
            raise Exception("to plot distance of, Length must be > 2")
        molecules = sum(self.get_molecules_with_journey_length(length), [])
        return [m.get_distance_of_journey(length) for m in molecules]

    def plot_distance_of_journies(self, length = 2, *args):
        return plt.hist(self.get_distance_of_journies(), *args)


    def approxiamte_diffusion_coefficients(self, journey_length = 4,
                                            bins = 200,
                                            p0 = None):
        if p0 is None:
            p0 = [5,5,.5]

        #at the moment, assumes 2 particle types
        molecules_by_simulation = self.get_molecules_with_journey_length(n = journey_length)
        displacements = [[_get_mean_square_displacement(molecule, journey_length-1) 
                                for molecule in _sim]  for _sim in molecules_by_simulation]

        histogram = np.histogram(list(chain.from_iterable(displacements)), 
                                bins)
        X, Y = histogram[1][:-1], histogram[0]
        number_of_tracks = np.sum(Y)
        delta = np.mean(np.diff(X))

        def distribution(X, D1, D2, ratio):
            DSTAR1 = 2 * self.step_time_in_seconds * D1
            DSTAR2 = 2 * self.step_time_in_seconds * D2
            return ratio/(1+ratio)*(number_of_tracks*delta)*1/(8*DSTAR1**3) * (X**(2)/2 * np.exp(-X/(2*DSTAR1))) + \
                       1/(ratio+1)*(number_of_tracks*delta)*1/(8*DSTAR2**3) * (X**(2)/2 * np.exp(-X/(2*DSTAR2))) 

        args, errors = optimize.curve_fit(distribution,
                            X, Y, p0 = p0)
        return args, [X, Y, distribution(X, *args)] 





def _get_mean_square_displacement(molecule, n = 3):
    dist_vect = molecule._square_displacement_vector(1)
    return (np.sum(dist_vect[range(n)]))
        