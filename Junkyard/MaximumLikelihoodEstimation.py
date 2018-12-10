
#Maximum Likelihood Estimationb
ms = two_species.get_molecules_with_journey_length(6)
def log_likelihood_for_two_species(molecules, p, sigma_1, sigma_2, step_time, box_size):
    from itertools import chain
    from numpy import log, prod
    mols = chain(*molecules) 
    loglikelihood = 0 
    As = []
    Bs = []
    ns = []
    N = len(molecules)
     
    expected_value_1 = box_size**2/(2*5*sigma_1*np.sqrt(step_time))
    expected_value_2= box_size**2/(2*5*sigma_2*np.sqrt(step_time))

    q1 = expected_value_1/(expected_value_1+1)
    q2 = expected_value_2/(expected_value_2+1)
        
    
    for molecule in mols:
        displacemenets = molecule._square_displacement_vector(1)
       
        A = np.prod(1/(np.sqrt(2*np.pi*sigma_1**2))*np.exp(- displacemenets / (2*sigma_1**2) ))
        B = np.prod(1/(np.sqrt(2*np.pi*sigma_2**2))*np.exp(- displacemenets / (2*sigma_2**2) ))
        
        As.append(A)
        Bs.append(B)
        
        ns.append(len(displacemenets))
    
    As = np.array(As)
    Bs = np.array(Bs)
    
#     p = 1/N * np.nansum(Bs/(As - Bs))
#     print(p)
    
    for A, B,n in zip(As, Bs, ns):
        _p1 = p*(q1**n*(1-q1))*A
        _p2 = (1-p)*(q2**n*(1-q2))*B
        loglikelihood += np.log(_p1+_p2)
    return loglikelihood
    