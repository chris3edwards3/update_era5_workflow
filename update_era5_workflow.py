"""
update_era5_workflow.py

Author: Chris Edwards
Copyright June 2020
License: BSD 3 Clause
Updated: June 2020

Workflow to update the ERA-5 historical simulation. This script:
1. Identifies the dates for the simulation
2. Starts the RAPID process for each region
3. Appends the resulting simulation onto an annual record netCDF file for each region
4. Creates a text file the records the last date of the simulation.
"""
# TODO: give a 2-week buffer for the initialization to catch up.
import os
import shutil
import sys
import re
from datetime import datetime
from datetime import timedelta
from imports_era5_workflow import append_era5_to_record
from imports_era5_workflow import run_era5_rapid_simulation

# ------------------------------------------------------------------------------
# main process
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    """
    arg1 = path to rapid executable
    arg2 = path to directory with LSM Grid (ERA-5 Runoff)
    arg3 = path to master rapid-io directory that contains the input and output folders
    arg4 = path to directory of log files
    arg5 = path to master directory of record files for each region
    """

    # accept the arguments
    rapid_executable_location = sys.argv[1]
    lsm_data_location = sys.argv[2]
    master_rapid_io_location = sys.argv[3]
    logs_dir = sys.argv[4]
    records_dir = sys.argv[5]

    # start logging & capture stdout/stderr to log/err file (instead of printing to console or command line)
    script_start_time = datetime.now()
    log_path = os.path.join(logs_dir, 'era5_rapid_simulation_' + script_start_time.strftime('%Y%m%d%H%M') + '.log')
    log = open(log_path, 'a')
    sys.stdout = log
    log_error_path = os.path.join(logs_dir,
                                  'era5_rapid_simulation_' + script_start_time.strftime('%Y%m%d%H%M') + '.err')
    log_error = open(log_error_path, 'a')
    sys.stderr = log_error
    print('Script update_era5_workflow.py initiated ' + script_start_time.strftime('%c'))

    # Figure out dates (previous run end date, simulation start and max end date, simulation year)
    print('\nFiguring out dates...')
    last_date_text_file_path = os.path.join(logs_dir, 'last_date_prev_sim.txt')
    last_date_text_file = open(last_date_text_file_path, 'r')
    last_date_prev_sim_str = last_date_text_file.read().strip()
    print('Last date of previous simulation: ' + last_date_prev_sim_str)
    simulation_start_datetime = datetime.strptime(last_date_prev_sim_str, '%Y%m%d') + timedelta(days=1)
    simulation_start_date_str = simulation_start_datetime.strftime('%Y%m%d')
    print('Simulation start date: ' + simulation_start_date_str)
    simulation_year_str = datetime.strftime(simulation_start_datetime, '%Y')
    max_simulation_end_datetime = datetime.strptime(simulation_year_str + '1231', '%Y%m%d')
    print('Max simulation end date: ' + max_simulation_end_datetime.strftime('%Y%m%d'))

    # Loop through and run RAPID on each region
    print('\nLooping through and running RAPID on each region...\n')
    input_regions = os.listdir(os.path.join(master_rapid_io_location, 'input'))
    for region in input_regions:
        run_era5_rapid_simulation(
            region,
            rapid_executable_location,
            lsm_data_location,
            master_rapid_io_location,
            last_date_prev_sim_str,
            simulation_start_datetime,
            max_simulation_end_datetime
        )
    print('\nDone with RAPID simulation for all regions.\n')

    # Identify actual last date of simulation
    print('Identifying actual last date of simulation...')
    actual_sim_end_date_str = ''
    first_region_output_dir = os.path.join(master_rapid_io_location, 'output', input_regions[0])
    for filename in os.listdir(first_region_output_dir):
        if filename.startswith('Qout') and re.search(simulation_start_date_str + 'to', filename):
            actual_sim_end_date_str = filename[-11:-3]
            print('Simulation end date: ' + actual_sim_end_date_str)
    if actual_sim_end_date_str == '':
        print('ERROR: Output file not found for ' + input_regions[0])
        raise Exception('Output file not found for ' + input_regions[0])

    # Append simulation onto record netCDF for each region
    for region in input_regions:
        print('\nAppending ERA-5 to record file for ' + region + '...')

        # Identify path for new Qout file
        region_output_dir = os.path.join(master_rapid_io_location, 'output', region)
        addition_file_path = ''
        for file in os.listdir(region_output_dir):
            if file.startswith('Qout') and file.endswith(actual_sim_end_date_str + '.nc'):
                addition_file_path = os.path.join(region_output_dir, file)
        if addition_file_path == '':
            print('ERROR: Qout file not found for ' + region + ' ' + actual_sim_end_date_str)
            raise Exception('Qout file not found for ' + region + ' ' + actual_sim_end_date_str)
        print('Path to new Qout file: ' + addition_file_path)

        # Identify path for record file
        record_file_name = 'Qout_era5_record_' + simulation_year_str + '.nc'
        region_record_dir = os.path.join(records_dir, region)
        record_file_path = os.path.join(region_record_dir, record_file_name)
        print('Path to record file: ' + record_file_path)

        # Create record file for simulation year or append to existing file
        if os.path.exists(record_file_path):
            append_era5_to_record(record_file_path, addition_file_path)
            print('Successfully appended ERA-5 to new record for ' + region + '\n')
        else:
            print(simulation_year_str + 'record file does not exist. Copying Qout file to make new record file...')
            if not os.path.exists(region_record_dir):
                os.mkdir(region_record_dir)
            shutil.copy(addition_file_path, record_file_path)
            print('Successfully created ' + simulation_year_str + ' record file for ' + region + '\n')

    # Update last_date_prev_sim.txt to show the final date of simulation run (YYYYMMDD)
    print('Writing new text file with simulation end date...')
    new_text_file = open(last_date_text_file_path, 'w')
    new_text_file.write(actual_sim_end_date_str)

    # Delete .err file if empty
    if os.path.getsize(log_error_path) == 0:
        print('Deleting empty .err file...')
        os.remove(log_error_path)

    # Finish ERA-5 workflow,
    script_end_time = datetime.now()
    print('\nWorkflow Finished! Total Runtime: ' + str(script_end_time - script_start_time))
