import os
import sys
import argparse
from ase.data import atomic_numbers

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
print(os.path.join(os.path.dirname(__file__), '..'))

from gslibs.utils.coordinates_io import lammpsdump_to_ase, ase_to_pdb

input_file = 'system.traj'
output_file = 'system.pdb'


print(f"Converting {input_file} to {output_file}")

atoms = lammpsdump_to_ase(input_file, step=1, stop=0)

specorder = 'O H C'
specorder = specorder.split()
symbols = []
atns = []
for species_index in atoms[0].numbers.tolist():
    if species_index > len(specorder):
        raise ValueError(f"Species index {species_index-1} is out of bounds for species order {specorder}")
    symbols.append(specorder[species_index-1])
    atns.append(atomic_numbers[symbols[-1]])
for atom in atoms:
    atom.set_atomic_numbers(atns)
    atom.set_chemical_symbols(symbols)

print(f"Read {len(atoms)} frames from {input_file}")


data = ase_to_pdb(atoms)

with open(output_file, 'w') as f:
    f.write(data)
print(f"Converted {input_file} to {output_file}")