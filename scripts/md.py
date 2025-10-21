import sys
import os
import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.singlemd import SingleMD

AUTH_FILE = None#os.environ.get('AUTH_FILE', None)

config  = yaml.safe_load(open('config-md.yaml', 'r'))

run_config = {}

run_config['system_name'] = config.get('system_name', None)
if run_config['system_name'] is None:
    raise ValueError("system_name must be specified in config-md.yaml")
run_config['run_name'] = config.get('run_name', 'Unnamed_run')
run_config['module'] = config.get('module', 'gromacs')
run_config['input_filename'] = config.get('input_filename', 'md.tpr' if run_config['module'] == 'gromacs' else 'lammps.in')

cfd = os.path.dirname(os.path.dirname(__file__))
run_config['input_root'] = config.get('input_root', cfd + f"/inputs")
run_config['run_root'] = config.get('run_root', cfd + "/md_runs")


run_config['settings'] = config.get('settings', {})
run_config['verbose'] = config.get('verbose', True)
run_config['additional_files'] = config.get('additional_files', [])
run_config['external_files'] = config.get('external_files', {})
run_config['copy_directories'] = config.get('copy_directories', {})
run_config['slurm_settings'] = config.get('slurm_settings', {})

mod = SingleMD(**run_config)

mod.execute(dry_run=config.get('dry_run', False))


    

