# qc-ga
We are using DEAP package to initiate and continue our evolution, and we are using ProjectQ to perform quantum computer simulations. 
Currently, we are using a set of genetic operators and selection procedure highly similar to [Potocek thing], but we allowed user to describe the topology of the quantum computer the proposed algorithms may be run on. 
We are still working on the project and we are planning to improve it further.

More details will be added later on.

## TODOS:
- Fix main after broken refactoring
- Save statevector (and noisy densitymatrix) of circuit outcome
- check remove consecutive inverse gates
- compare fidelity between best noisy LRSP circuit and best GA individual

## Known issues

- does not filter empty/trivial circuits and gates
- does not combine e.g. sqrtx gates