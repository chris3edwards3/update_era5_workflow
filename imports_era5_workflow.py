"""
imports_era5_workflow.py

Author: Chris Edwards
Copyright June 2020
License: BSD 3 Clause
Updated: June 2020

1. Appends ERA-5 RAPID simulation onto a master record netcdf
2. Runs rapid for ERA-5 Historical Simulation initializing the flow-rates based on the end of previous simulation
"""
import netCDF4 as nc
import numpy as np
import os
from RAPIDpy.inflow import run_lsm_rapid_process


def append_era5_to_record(record_file_path, addition_file_path):
    record_netcdf = nc.Dataset(record_file_path, mode='a')
    addition_netcdf = nc.Dataset(addition_file_path, mode='r')

    # read the time and flow variables of both files
    time_record_array = record_netcdf.variables['time'][:]
    time_record_list = time_record_array.tolist()
    time_addition_array = addition_netcdf.variables['time'][:]
    time_addition_list = time_addition_array.tolist()
    flow_record_array = record_netcdf.variables['Qout'][:]
    flow_addition_array = addition_netcdf.variables['Qout'][:]

    # Check for duplicate time-steps
    print('Checking for duplicate time-steps in record and new simulation...')
    time_duplicates_count = len(set(time_record_list) & set(time_addition_list))
    print('Duplicate time-step count: ' + str(time_duplicates_count))

    print('Deleting {} overlapping time-steps from the addition...'.format(time_duplicates_count))
    time_addition_array_keep = time_addition_array[time_duplicates_count:]
    flow_addition_array_keep = flow_addition_array[time_duplicates_count:]

    # Appending new time-steps to new array
    print('Appending additional time-steps to record netCDF...')
    time_new_total_array = np.append(time_record_array, time_addition_array_keep, axis=0)
    flow_new_total_array = np.append(flow_record_array, flow_addition_array_keep, axis=0)

    # Saving new arrays to record netCDF file
    record_netcdf.variables['Qout'][:] = flow_new_total_array
    record_netcdf.variables['time'][:] = time_new_total_array
    print('New time-steps saved to netCDF')


def run_era5_rapid_simulation(region, rapid_executable_location, lsm_data_location, master_rapid_io_location,
                              last_date_prev_sim, simulation_start_datetime, simulation_end_datetime):
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
        if file.endswith(last_date_prev_sim + '.csv') and file.startswith('qinit_era5'):
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
