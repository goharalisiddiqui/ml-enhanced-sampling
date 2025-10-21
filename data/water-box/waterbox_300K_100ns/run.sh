#! /bin/bash
#SBATCH -J MD
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH -p zencloud
#SBATCH --mem=8G
#SBATCH --time=100:00:00
#SBATCH --export=ALL
#SBATCH -o ./slurm_logs/slurm-%J.out
#SBATCH -e ./slurm_logs/slurm-%J.err

####### PREPARE ENV #######
echo "Loading modules from $SLURM_PRESCRIPT_LAMMPS"
source $SLURM_PRESCRIPT_LAMMPS
########################################

unset $pref
if [ ! -z "${SLURM_JOB_ID}" ]; then
    echo "Running on compute node"
    pref='srun'
    mkdir -p slurm_logs
else 
    echo "Running on local machine"
    pref=''
fi

if [ ! -f "../initialization/waterbox.restart" ]; then
  echo "Initial restart file not found! Exiting."
  exit 1
fi

# Remove all files and folders except input_files folder
find . -maxdepth 1 ! -name 'input_files' ! -name '.' ! -name 'run.sh' -exec rm -rf {} +
cp ../initialization/waterbox.restart .
cp  input_files/lammps.in ../traj_tools/create_pdb.py .
$pref lmp -in lammps.in