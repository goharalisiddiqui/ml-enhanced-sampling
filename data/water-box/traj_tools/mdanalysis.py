import sys
sys.path.append('/mnt/system/spack_nfs/spack_24Q2/spack_main/var/spack/environments/python-3p9-torch2-cuda12-24Q2/.spack-env/view/lib/python3.11/site-packages')

import numpy as np

import MDAnalysis as mda
import MDAnalysis.transformations as trans

from tqdm import tqdm

import ase
from ase import io

TYPES_TO_ATOMIC_NUMBERS = [8,1,6] # O, H, C

u = mda.Universe("../waterbox.data", "../system.xtc")
for i in range(len(u.atoms)):
    u.atoms[i].type = str(TYPES_TO_ATOMIC_NUMBERS[int(u.atoms[i].type) - 1])
    dir(u.atoms[i])

ag = u.select_atoms("type 6")
mol = u.select_atoms("all")
water = u.select_atoms("type 1 or type 8")
transforms = [
    trans.center_in_box(ag, center='geometry'),
    trans.wrap(water, compound='residues')
    ]
u.trajectory.add_transformations(*transforms)

atns = [int(atom.type) for atom in mol.atoms]

# print(u.dimensions)
# ewdsda

mol_traj = []
for idx in tqdm(range(len(u.trajectory))):
    u.trajectory[idx]
    # Create the ASE structure
    structure = ase.Atoms(numbers=atns, 
                          positions=mol.atoms.positions,
                          cell=u.dimensions[:3],
                          pbc=[True, True, True]
                          )

    # Retain topology information
    residues = ["SOL" if r.type in ['1','8'] else "UNK" for r in mol.atoms]
    structure.set_array('residuenames', np.array(residues))
    # resids = [r.residue.resid for r in mol.atoms]
    # atomnames = [str(a.name) for a in mol.atoms]
    # structure.set_array('residuenumbers', np.array(resids))
    # structure.set_array('atomtypes', np.array(atomnames))

    mol_traj.append(structure)

# Save the trajectory as an PDB file
io.write("waterbox.pdb", mol_traj, format='proteindatabank', append=False)