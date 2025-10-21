#! /bin/bash
#SBATCH -J CE
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 16
#SBATCH -p gpucloud
#SBATCH --mem=100G
#SBATCH --gres=shard:1
#SBATCH --time=100:00:00
#SBATCH --export=ALL
#SBATCH -o ./slurm_logs/slurm-%J.out
#SBATCH -e ./slurm_logs/slurm-%J.err

unset $pref
if [ ! -z "${SLURM_JOB_ID}" ]; then
    echo "Running on compute node"
    pref='srun'
    mkdir -p slurm_logs

    ####### PREPARE ENV #######
    echo "Loading conda env"
    conda activate .cenv
    ########################################
else 
    echo "Running on local machine"
    pref=''
fi

#Read command line arguments
while getopts d flag
do
    case "${flag}" in
        d) debug=1;;
    esac
done

if [ "$debug" == 1 ]; then
    $pref python collective_encoder/engine.py --config config-cv.yaml --debug
else
    $pref python collective_encoder/engine.py --config config-cv.yaml
fi