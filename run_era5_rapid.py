"""
update_era5_workflow.py

Author: Chris Edwards
Copyright June 2020
License: BSD 3 Clause
Updated: June 2020

Script to run ERA-5 RAPID simulation for one whole year of ERA-5 Runoff data.
To run the script, give 6 additional arguments:
    1. path to rapid executable
    2. path to directory with LSM Grid (ERA-5 Runoff)
    3. path to master rapid-io directory that contains the input and output folders
        (the input folder should have sub-folders for each region)
    4. path to master directory of record files for each region (this path should have sub-folders for each region)
    5. path to directory of log files
    6. year to run (eg: 2020)
"""
import os
import sys
from datetime import datetime, timedelta
from RAPIDpy.inflow import run_lsm_rapid_process


def run_era5_rapid_simulation(region, rapid_executable_location, lsm_data_location, master_rapid_io_location,
                              prev_sim_end_date_str, simulation_start_datetime, simulation_end_datetime):
    print('Region: ' + region)

    # Define rapid input and output folder for specific region
    rapid_input_location = os.path.join(master_rapid_io_location, 'input', region)
    print('Rapid Input Folder: ' + rapid_input_location)
    rapid_output_location = os.path.join(master_rapid_io_location, 'output', region)
    if not os.path.exists(rapid_output_location):
        print('Creating Output Folder...')
        os.makedirs(rapid_output_location)
    print('Rapid Output Folder: ' + rapid_output_location)

    # Check for initial flows file
    initial_flows_file = ''
    for file in os.listdir(rapid_input_location):
        if file.endswith(prev_sim_end_date_str + '.csv') and file.startswith('qinit_era5'):
            initial_flows_file = os.path.join(rapid_input_location, file)
            print('Initial FLows File: ' + initial_flows_file)
    if initial_flows_file == '':
        print('ERROR: Initial Flows File not found for the region ' + region)
        raise Exception('Initial Flows File not found for the region ' + region)

    # Run RAPID
    print('Starting RAPID process for ' + region + '...\n')
    run_lsm_rapid_process(
        rapid_executable_location=rapid_executable_location,
        lsm_data_location=lsm_data_location,  # folder containing ERA-5 runoff data
        rapid_input_location=rapid_input_location,
        rapid_output_location=rapid_output_location,
        initial_flows_file=initial_flows_file,
        simulation_start_datetime=simulation_start_datetime,
        simulation_end_datetime=simulation_end_datetime,  # will stop at last date of available runoff grid
        run_rapid_simulation=True,  # if you want to run RAPID after generating inflow file
        generate_rapid_namelist_file=False,  # if you want to run RAPID manually later
        generate_initialization_file=True,  # if you want to generate qinit file from end of RAPID simulation
        use_all_processors=False,  # defaults to use all processors available
        num_processors=1  # you can change this number if use_all_processors=False
    )
    print('------------------------------\n')


# ------------------------------------------------------------------------------
# main process
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    """
    arg1 = path to rapid executable
    arg2 = path to directory with LSM Grid (ERA-5 Runoff)
    arg3 = path to master rapid-io directory that contains the input and output folders
    arg4 = path to master directory of record files for each region 
    arg5 = path to directory of log files
    arg6 = year to run (eg: 2020)
    """

    # accept the arguments
    rapid_executable_location = sys.argv[1]
    lsm_data_location = sys.argv[2]
    master_rapid_io_location = sys.argv[3]
    records_dir = sys.argv[4]
    logs_dir = sys.argv[5]
    simulation_year_str = sys.argv[6]

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
    simulation_start_date_str = simulation_year_str + '0101'
    simulation_start_datetime = datetime.strptime(simulation_start_date_str, '%Y%m%d')
    print('Simulation start date: ' + simulation_start_date_str)
    simulation_end_date_str = simulation_year_str + '1231'
    simulation_end_datetime = datetime.strptime(simulation_end_date_str, '%Y%m%d')
    print('Simulation end date: ' + simulation_end_date_str)
    prev_sim_end_datetime = simulation_start_datetime - timedelta(days=1)
    prev_sim_end_date_str = prev_sim_end_datetime.strftime('%Y%m%d')
    print('Last date of previous simulation: ' + prev_sim_end_date_str)

    # Loop through and run RAPID on each region
    print('\nLooping through and running RAPID on each region...\n')
    input_regions = os.listdir(os.path.join(master_rapid_io_location, 'input'))
    for region in input_regions:
        run_era5_rapid_simulation(
            region,
            rapid_executable_location,
            lsm_data_location,
            master_rapid_io_location,
            prev_sim_end_date_str,
            simulation_start_datetime,
            simulation_end_datetime
        )
    print('\nDone with RAPID simulation for all regions.\n')

    # Delete .err file if empty
    if os.path.getsize(log_error_path) == 0:
        print('Deleting empty .err file...')
        os.remove(log_error_path)

    # Finish ERA-5 workflow,
    script_end_time = datetime.now()
    print('\nWorkflow Finished! Total Runtime: ' + str(script_end_time - script_start_time))
