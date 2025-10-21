import sys
import os 
from typing import List, Dict
import http.client, urllib
from collections import OrderedDict
from time import sleep
import subprocess
import shutil
import pickle

from gslibs.utils.filesystem import *
from gslibs.utils.coordinates_io import *

class SingleMD:
    def __init__(self, system_name: str,
                 run_name: str, 
                 input_root: str = os.path.dirname(os.path.dirname(__file__)) + "/input",
                 run_root: str = os.path.dirname(os.path.dirname(__file__)) + "/runs",
                 module: str = 'lammps',
                 verbose: bool = False,
                 push_notification_credentials_file: str = None,
                 additional_files: List[str] = [],
                 external_files: Dict = {},
                 copy_directories: Dict = {},
                 initial_structure_file: str = None,
                 input_filename: str = "lammps.in",
                 settings = {},
                 slurm_settings = {},
                 ):
        assert not None in [system_name, run_name, input_root, verbose]
        assert input_root.startswith('/'), "input root must be an absolute path"
        assert run_root, "run root must be a non-empty string"
        system_input_dir = os.path.join(input_root, system_name, module)
        assert os.path.exists(system_input_dir), f"Input directory {system_input_dir} not found."
        assert isinstance(settings, dict), "Settings must be a dictionary."
        
        if initial_structure_file is not None:
            assert initial_structure_file.startswith('/'), "Initial structure file must be an absolute path."
            assert os.path.exists(initial_structure_file), f"Initial structure file {initial_structure_file} not found."
        
        ###################################################
        # Check if all necessary input files are present
        ###################################################
        input_files = [input_filename]
        input_files += additional_files
        input_files += list(external_files.values())
        check = [os.path.exists(os.path.join(system_input_dir, file)) for file in input_files]
        assert all(check), f"Single MD: Missing input files {[a for a in input_files if check[input_files.index(a)] == False]}"
        
        ###################################################
        # Make the run directory
        ###################################################
        if not os.path.exists(run_root):
            os.makedirs(run_root)
        run_dir = os.path.join(run_root, run_name)
        
        ###################################################
        # Copy stdout and stderr to a log file
        ###################################################
        log_file = os.path.join(run_dir, f"singlemd.log")
        if os.path.exists(log_file):
            backup_move(log_file)
        tee = subprocess.Popen(["tee", log_file], stdin=subprocess.PIPE)
        # Cause tee's stdin to get a copy of our stdin/stdout (as well as that
        # of any child processes we spawn)
        os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
        os.dup2(tee.stdin.fileno(), sys.stderr.fileno())
        
        ###################################################
        # Check if iterations exist from previous run
        ###################################################
        if os.path.exists(run_dir):
            raise ValueError(f"Single MD: Run directory {run_dir} already exists.")
            # backup_move(run_dir)
            # print(f"Single MD: Backed up existing run directory {run_dir}") if verbose else None
        os.makedirs(run_dir, exist_ok=True)
            
        ###################################################
        # Set class variables
        ###################################################
        self.system_name = system_name
        self.system_input_dir = system_input_dir
        self.input_filename = input_filename
        self.run_name = run_name
        self.input_root = input_root
        self.run_root = run_root
        self.run_dir = run_dir
        self.module = module
        self.verbose = verbose
        self.additional_files = additional_files
        self.external_files = external_files
        self.copy_directories = copy_directories
        self.initial_structure_file = initial_structure_file
        self.meta = settings
        self.slurm_settings = slurm_settings
        self.md = None
        self.file_dir = os.path.dirname(os.path.abspath(__file__))
        

        ###################################################
        # Collect meta data about the structure
        ###################################################
        if initial_structure_file is not None:
            structure = any_to_ase(initial_structure_file)
            if len(structure) != 1:
                raise ValueError(f"Single MD: More than one structure found in initial structure file {initial_structure_file}.")
            structure = structure[0]
            coordinates = structure.get_positions()
            cell = structure.get_cell()
            if (cell == 0).all(): # no cell found, make one
                buffer = 5.0
                xmin, ymin, zmin = coordinates.min(axis=0) 
                xmax, ymax, zmax = coordinates.max(axis=0)
                x, y, z = xmax, ymax, zmax # FIXME: Find a better way to do this
                x, y, z = x + buffer, y + buffer, z + buffer
                x, y, z = int(x), int(y), int(z)
                cell = array([[x, 0, 0], [0, y, 0], [0, 0, z]]).astype(float)
            self.meta["cell"] = cell
        
        ###################################################
        # Setting up push notifications
        ###################################################
        if push_notification_credentials_file is not None and os.path.exists(push_notification_credentials_file):
            cred = {}
            with open(push_notification_credentials_file, "r") as f:
                lines = f.readlines()
                for line in lines:
                    key, value = line.strip().split("=")
                    cred[key] = value
            if all([key in cred for key in ["pushover_token", "pushover_user"]]):
                self.push_creds = cred 
                print("Single MD: Push notifications enabled.") if verbose else None
            else:
                print("Single MD: Credentials file for push notifications present but unuseable.") if verbose else None
        else:
            print("Single MD: Could not get credentials for push notification.") if verbose else None  


    def send_push_notification(self, message):
        if not hasattr(self, "push_creds"):
            return
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": self.push_creds["pushover_token"],
            "user": self.push_creds["pushover_user"],
            "message": message,
        }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

    def execute(self, dry_run: bool = False):
        if self.md is None:
            self.set_mdengine()
        
        self.md.run(dry_run=dry_run)
        print(f"Single MD {self.run_name}: MD engine started.")
        # self.wait_for_runs([self.md])
        self.send_push_notification(f"Single MD {self.run_name}: MD engine finished.")
    
    def set_slurm_settings(self):
        self.md.slurm_preamble = [
            'conda deactivate || true',
            'module purge',
        ]
        
    
    def set_mdengine(self):
        self.md = None
        md_dir = os.path.abspath(os.path.join(self.run_dir, "md_single"))
        input_file = os.path.abspath(os.path.join(self.system_input_dir, self.input_filename))
        if self.module == "lammps":
            from gslibs.drivers.mdengines.lammps import lammps_driver
            

            md = lammps_driver(input_file = input_file, 
                                    run_name=self.run_name + f"_single",
                                    run_dir=md_dir,
                                    verbose=self.verbose,
                                    meta=self.meta,
                                    slurm_settings=self.slurm_settings,
                                    )
            if self.initial_structure_file is not None:
                md.add_coordinates_file(source=self.initial_structure_file, dest="data.lammps")
        elif self.module == "gromacs":
            from gslibs.drivers.mdengines.gromacs import gromacs_driver
            md = gromacs_driver(input_file=input_file,
                                 run_name=self.run_name + f"_single",
                                 run_dir=md_dir,
                                 verbose=self.verbose,
                                 meta=self.meta)
        else:
            raise ValueError(f"Single MD {self.run_name}: MD engine {self.module} not supported yet.")
        for fn, path in self.external_files.items():
            if not os.path.exists(path):
                raise ValueError(f"Single MD {self.run_name}: External file {path} not found.")
            md.add_binary_file(source=path, dest=fn)
        for fn, path in self.copy_directories.items():
            if not os.path.exists(path):
                raise ValueError(f"Single MD {self.run_name}: Copy directory {path} not found.")
            md.add_copy_directory(source=path, dest=fn)
        for fn in self.additional_files:
            path = os.path.join(self.system_input_dir, fn)
            if not os.path.exists(path):
                raise ValueError(f"Single MD {self.run_name}: Additional file {fn} at {path} not found.")
            md.add_binary_file(source=path, dest=fn)
            # md.uses_plumed(plumed_script_path='plumed.dat')
        self.md = md
        self.set_slurm_settings()
        
    @staticmethod
    def wait_for_runs(runs):
        for run in runs:
            while run.is_job_running():
                sleep(5)
