'''
This script demonstrates simulation results extraction for the synthetic operation data generation.
It iteratively extracts the raw CSV outputs from the simulation and saves the results in a structured way.
Note that the actual structure and contents of new simulations may vary.
'''

import os
import pandas as pd
from shutil import copyfile

def get_full_paths(dir_path, absolute=True):
    if absolute:
        return [os.path.abspath(os.path.join(dir_path, sub_path)) for sub_path in os.listdir(dir_path)]
    else:
        return [os.path.join(dir_path, sub_path) for sub_path in os.listdir(dir_path)]


# Main routine
if __name__ == "__main__":
    ls_effs = ['Standard'] # Extract simulation results for efficiency level(s).
    ls_climates = ['2A']                  # Extract simulation results for climate zone(s).
    dir_all_sims = os.path.join('..', 'Models', '3~OSWs')
    dir_simulations = os.path.join('.', 'Models', '3~OSWs', f'efficiency_level_{ls_effs[0]}', f'SmallOfficeDetailed_90.1-2013_{ls_climates[0]}') # Extract simulation results for MediumOfficeDetailed models.
    dir_cleaned = os.path.join('..', 'clean_extraction')
    count = 0
    for dir_eff in get_full_paths(dir_all_sims):
        str_eff = dir_eff.split('_')[-1]
        print(f'------> Current eff: {str_eff}')
        for dir_clm in get_full_paths(dir_eff):
            str_clm = dir_clm.split('_')[-1]
            print(f'   ------> Current climate: {str_clm}')
            for dir_yr in get_full_paths(dir_clm):
                count += 1
                str_yr = dir_yr.split('_')[-1]
                print(f'      ------> Current year: {str_yr}')
                for dir_run in get_full_paths(dir_yr):
                    str_run = dir_run.split('\\')[-1]
                    print(f'         ------> Current run: {str_run}')
                    dir_all_reports = os.path.join(dir_run, 'reports')
                    if os.path.exists(dir_all_reports):
                        for dir_report in get_full_paths(dir_all_reports):
                            prefix = f'{str_eff}_{str_clm}_{str_yr}_{str_run}~'
                            new_name = os.path.basename(dir_report).replace('export_meterto_csv_report_', '').replace('_ZoneTimestep', '')
                            new_name = new_name.replace('export_variableto_csv_report_', '').replace('_ZoneTimestep', '')
                            new_file = os.path.join(dir_cleaned, prefix+new_name)
                            if os.path.exists(new_file):
                                next
                            else:
                                copyfile(dir_report, new_file)