#! /bin/bash
#SBATCH -J MD
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH -p zencloud
#SBATCH --mem=8G
#SBATCH --time=100:00:00
#SBATCH --export=ALL
#SBATCH -o ./slurm.out
#SBATCH -e ./slurm.err

####### PREPARE ENV #######
echo "Loading modules from $SLURM_PRESCRIPT_LAMMPS"
source $SLURM_PRESCRIPT_LAMMPS
########################################

unset $pref
if [ ! -z "${SLURM_JOB_ID}" ]; then
    echo "Running on compute node"
    pref='srun'
else 
    echo "Running on local machine"
    pref=''
fi

# Remove all files and folders except input_files folder
find . -maxdepth 1 ! -name 'input_files' ! -name '.' ! -name 'run.sh' -exec rm -rf {} +
cp ../initialization/MAPI.restart .
cp input_files/lammps.in .
cp -r input_files/myp2 .
$pref lmp -in lammps.in