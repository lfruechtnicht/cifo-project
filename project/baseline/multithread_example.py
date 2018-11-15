import os
import datetime
import multiprocessing
import itertools

import logging
import numpy as np

from sklearn import datasets
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

import utils as uls
from problems.ANNOP import ANNOP
from ANN.ANN import ANN, softmax, sigmoid
from algorithms.genetic_algorithm import GeneticAlgorithm
from algorithms.simulated_annealing import SimulatedAnnealing


# setup logger
file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "LogFiles/" + (str(datetime.datetime.now().date()) + "-" + str(datetime.datetime.now().hour) + \
            "_" + str(datetime.datetime.now().minute) + "_log.csv"))
logging.basicConfig(filename=file_path, level=logging.DEBUG, format='%(name)s,%(message)s')


file_name= "LogFiles/" + "custom_example_" + str(datetime.datetime.now().date()) + "-" + str(datetime.datetime.now().hour) + \
            "_" + str(datetime.datetime.now().minute) + "_log.csv"

header_string = "Seed,N_gen,PS,PC,PM,radius,Pressure,Fitness,UnseenAccuracy,Time"
with open(file_name, "a") as myfile:
    myfile.write(header_string + "\n")


# ++++++++++++++++++++++++++
# THE DATA
# restrictions:
# - MNIST digits (8*8)
# - 33% for testing
# - flattened input images
# ++++++++++++++++++++++++++
digits = datasets.load_digits()
flat_images = np.array([image.flatten() for image in digits.images])

# split data
X_train, X_test, y_train, y_test = train_test_split(flat_images, digits.target, test_size=0.33, random_state=0)

# setup benchmarks
n_runs = [2] # Always a single int
n_genes = [x for x in range(10,20)]
validation_p = .2
validation_threshold = .07

# Genetic Algorithm setup
pss = [50]
p_cs = [.8]
p_ms = [0.9]
radiuses= [.2]
pressures = [.2]

# Simulated Annealing setup
ns = pss
control = [2]
update_rate = [0.9]

def algo_run(n_gen,ps,p_c,p_m,radius,pressure,n_runs):

    for seed in range(n_runs):
        random_state = uls.get_random_state(seed)
        start_time = datetime.datetime.now()

        #++++++++++++++++++++++++++
        # THE ANN
        # restrictions:
        # - 2 h.l.
        # - Softmax a.f. at output
        # - 20%, out of remaining 67%, for validation
        #++++++++++++++++++++++++++
        # ann's architecture
        hidden_architecture = np.array([[10, sigmoid], [10, sigmoid]])
        n_weights = X_train.shape[1]*10*10*len(digits.target_names)
        # create ann
        ann_i = ANN(hidden_architecture, softmax, accuracy_score, (X_train, y_train), random_state, validation_p, digits.target_names)

        #++++++++++++++++++++++++++
        # THE PROBLEM INSTANCE
        # - optimization of ANN's weights is a COP
        #++++++++++++++++++++++++++
        ann_op_i = ANNOP(search_space=(-2, 2, n_weights), fitness_function=ann_i.stimulate,
                         minimization=False, validation_threshold=validation_threshold)

        #++++++++++++++++++++++++++
        # THE SEARCH
        # restrictions:
        # - 5000 offsprings/run max*
        # - 50 offsprings/generation max*
        # - use at least 5 runs for your benchmarks
        # * including reproduction
        #++++++++++++++++++++++++++
        alg = GeneticAlgorithm(ann_op_i, random_state, ps, uls.parametrized_tournament_selection(pressure),
                          uls.one_point_crossover, p_c, uls.parametrized_ball_mutation(radius), p_m)
        alg.initialize()
        # initialize search algorithms
        ########Search   ############################ LOG \/ ########################
        alg.search(n_iterations=n_gen, report=False, log=True)

        ############# Evaluate unseen fitness ##################
        ann_i._set_weights(alg.best_solution.representation)
        y_pred = ann_i.stimulate_with(X_test, False)
        accuracy = accuracy_score(y_test, y_pred)
        time_elapsed = datetime.datetime.now() - start_time
        # Create result string
        result_string = ",".join(
            [str(seed+1)+"/"+str(n_runs) , str(n_gen), str(ps), str(p_c), str(p_m), str(radius), str(pressure),
             str(alg.best_solution.fitness), str(accuracy),str(time_elapsed)])
        # Write result to a file
        with open(file_name, "a") as myfile:
            myfile.write(result_string + "\n")
        # Output result to terminal
        print(header_string)
        print(result_string)


possible_values = list(itertools.product(*[n_genes,pss,p_cs,p_ms,radiuses,pressures,n_runs]))
core_count = multiprocessing.cpu_count()
print("All possible combinations generated:")
print(possible_values)
print("Number of cpu cores: "+str(core_count))

####### Magic appens here ########
pool = multiprocessing.Pool(core_count)
results = pool.starmap(algo_run, possible_values)
