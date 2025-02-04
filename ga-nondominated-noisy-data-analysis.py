from qiskit.providers.aer import QasmSimulator
import pickle
import os
import re
from threading import Thread
from numpy import *
from matplotlib import pyplot as plt
import pandas as pd
from deap.tools.emo import sortNondominated
from qiskit import *
from qiskit.quantum_info import state_fidelity

from tools import *
from individual import Individual


def load_files_by_name(basedir):
    loaded = {}
    for name in next(os.walk(basedir))[2]:
        with open(os.path.join(basedir, name), 'rb') as file:
            loaded[name] = pickle.load(file)
    return loaded


basedir = 'states/5_qubits'
states = load_files_by_name(basedir)


states_with_pop = {}
for name, state in states.items():
    try:
        with open(f'performance_data/5QB/400POP/500-30000GEN-{name}.pop', 'rb') as f:
            states_with_pop[name] = {'state': state, 'pop': pickle.load(f)}
    except:
        pass


def uniqBy(l, f):
    uniq_so_far = []
    uniq_so_far_mapped = []
    for c in l:
        d = f(c)
        if not d in uniq_so_far_mapped:
            uniq_so_far_mapped.append(d)
            uniq_so_far.append(c)
    return uniq_so_far


lrsp_circs = load_files_by_name('5QB-LRSP-fronts')

lrsp_circs_uniq = {name: uniqBy(circs, lambda c: c.circuit)
                   for name, circs in lrsp_circs.items()}


backend = AerSimulator(method='density_matrix', noise_model=noise_model)
backend = Aer.get_backend('qasm_simulator')
backend = QasmSimulator(method='density_matrix', noise_model=noise_model)


def total_cnots(circ):
    cnots = 0
    for gate in circ:
        if (gate[1] == CNOT):
            cnots += 1
    return cnots


assert states.keys() == lrsp_circs_uniq.keys()


def create_datadir(datadir):
    if os.path.exists(datadir):
        dirname, index = re.match(
            '^(5QB[A-Za-z\-]+)_?(\d+?)?$', datadir).groups()
        nextdatadir = f'{dirname}_{int(index or 0) + 1}'
        return create_datadir(nextdatadir)
    else:
        os.mkdir(datadir)
        return datadir


def multithread_chunks(data, chunks, run):
    treds = []
    for i in range(chunks):
        chunk = list(data)[i::chunks]
        print(len(chunk))
        t = Thread(target=run, args=[chunk])
        t.start()
        treds.append(t)

    for t in treds:
        t.join()


def noisy_simulation_density_matrix(circ):
    circ.save_density_matrix(label='density_matrix')
    #result = backend.run(circ).result()
    result = execute(circ, backend,
                     coupling_map=connectivity,
                     noise_model=noise_model).result()
    return result.data()['density_matrix']


def run_ga_nondominated_noisy_fids(datadir):
    def _(data):
        for name, obj in data:
            data = []
            state = obj['state']
            pop = sortNondominated(obj['pop'], len(
                obj['pop']), first_front_only=True)[0]
            pop = uniqBy(pop, lambda c: c.circuit)
            for ind in pop:
                permutation = ind.getPermutationMatrix()
                permutation = np.linalg.inv(permutation)
                cnots = total_cnots(ind.circuit)
                ind_data = {'runs': [],
                            'permutation': permutation, 'cnots': cnots}
                for i in range(100):  # find the best circuit from noisy results
                    circ = ind.toQiskitCircuit()
                    circ.measure_all()
                    circ = transpile(circ, fake_machine, optimization_level=0)
                    transpile_permutation = get_permutation(circ)
                    density_matrix_noisy = noisy_simulation_density_matrix(
                        circ)
                    ind_data['runs'].append(
                        {'transpile_permutation': transpile_permutation, 'density_matrix_noisy': density_matrix_noisy})
                data.append(ind_data)
                print(f'finished an individual for {name}')

            f = open(os.path.join(datadir, name), 'wb')
            pickle.dump(data, f)
            f.close()
            print(f'finished {name}')
    return _


if __name__ == '__main__':
    datadir = create_datadir('5QB-GA-nondominated-noisy-data')
    multithread_chunks(states_with_pop.items(), 4,
                       run_ga_nondominated_noisy_fids(datadir))
    # run_ga_nondominated_noisy_fids(datadir)(states_with_pop.items())
