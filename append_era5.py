"""
append_era5.py

Author: Chris Edwards
Copyright June 2020
License: BSD 3 Clause
Updated: June 2020

Script to append ERA-5 RAPID simulation onto a master netCDF, eg. add 2019 to the 1979-2018 file.
To run the script, give 3 additional arguments:
    1. Path to output directory containing new Qout netCDFs (this path should have sub-folders for each region)
    2. Path to directory with complete historical netCDFs (this path should have sub-folders for each region)
        This path may be the same as argument 1
    3. Year that is being added (eg: 2019)

Note: the complete historical netCDF's should have a time dimension with UNLIMITED length, or this won't work.
"""
import netCDF4 as nc
import numpy as np
import os
import sys
from datetime import datetime


def append_era5_to_record(record_file_path, addition_file_path):
    record_netcdf = nc.Dataset(record_file_path, mode='a')
    addition_netcdf = nc.Dataset(addition_file_path, mode='r')

    # Read the time and flow variables of both files
    time_record_array = record_netcdf.variables['time'][:]
    time_record_list = time_record_array.tolist()
    time_addition_array = addition_netcdf.variables['time'][:]
    time_addition_list = time_addition_array.tolist()
    flow_record_array = record_netcdf.variables['Qout'][:]
    flow_addition_array = addition_netcdf.variables['Qout'][:]

    # Determine if the row dimension in Qout array is time or rivid
    record_flow_rows_are_time = False
    if np.size(flow_record_array, 0) == np.size(time_record_array, 0):
        record_flow_rows_are_time = True
    print('Record flow array rows are time:', record_flow_rows_are_time)
    addition_flow_rows_are_time = False
    if np.size(flow_addition_array, 0) == np.size(time_addition_array, 0):
        addition_flow_rows_are_time = True
    print('Addition flow array rows are time:', addition_flow_rows_are_time)

    # Check for duplicate time-steps
    print('Checking for duplicate time-steps in record and new simulation...')
    time_duplicates_count = len(set(time_record_list) & set(time_addition_list))
    print('Duplicate time-step count: ' + str(time_duplicates_count))

    # Create new addition arrays that remove duplicate time-steps, if any
    print('Removing {} overlapping time-steps from the addition...'.format(time_duplicates_count))
    time_addition_array_keep = time_addition_array[time_duplicates_count:]
    flow_addition_array_keep = []
    if addition_flow_rows_are_time:
        flow_addition_array_keep = flow_addition_array[time_duplicates_count:, :]
    else:
        flow_addition_array_keep = flow_addition_array[:, time_duplicates_count:]

    # Create new array with record and addition timesteps
    print('Appending on addition time-step array to time variable...')
    time_new_total_array = np.append(time_record_array, time_addition_array_keep, axis=0)
    flow_new_total_array = []
    if record_flow_rows_are_time and addition_flow_rows_are_time:
        print('Appending on addition flow array as new rows to Qout variable...')
        flow_new_total_array = np.append(flow_record_array, flow_addition_array_keep, axis=0)
    elif record_flow_rows_are_time and not addition_flow_rows_are_time:
        print('Appending on addition flow array transpose as new rows to Qout variable...')
        flow_new_total_array = np.append(flow_record_array, np.transpose(flow_addition_array_keep), axis=0)
    elif not record_flow_rows_are_time and addition_flow_rows_are_time:
        print('Appending on addition flow array transpose as new columns to Qout variable...')
        flow_new_total_array = np.append(flow_record_array, np.transpose(flow_addition_array_keep), axis=1)
    elif not record_flow_rows_are_time and not addition_flow_rows_are_time:
        print('Appending on addition flow array as new columns to Qout variable...')
        flow_new_total_array = np.append(flow_record_array, flow_addition_array_keep, axis=1)

    # Saving new arrays to record netCDF file
    print('Writing time variable to netCDF...')
    record_netcdf.variables['time'][:] = time_new_total_array
    print('Writing Qout variable to netCDF')
    record_netcdf.variables['Qout'][:] = flow_new_total_array
    print('New time-steps saved to netCDF')


# ------------------------------------------------------------------------------
# main process
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    """
    arg1 = path to Output folder containing recently computed Qout netCDFs
    arg2 = path to directory with master netCDFs
    arg4 = path to directory of log files
    arg3 = year that is being added (eg: 2019)
    """

    # Accept the arguments
    output_dir = sys.argv[1]
    master_era5_dir = sys.argv[2]
    logs_dir = sys.argv[3]
    year_to_add = sys.argv[4]

    # Start logging & capture scdtdout to log file (instead of printing to console or command line)
    script_start_time = datetime.now()
    log_path = os.path.join(logs_dir, 'append_era5_' + script_start_time.strftime('%Y%m%d%H%M') + '.log')
    log = open(log_path, 'a')
    sys.stdout = log
    print('Script append_era5.py initiated ' + script_start_time.strftime('%c') + '\n')

    # Figure out dates that show up in file-names
    addition_start_date = year_to_add + '0101'
    addition_end_date = year_to_add + '1231'
    record_end_date = str(int(year_to_add) - 1) + '1231'
    print('Addition start & end dates: ' + addition_start_date + ' to ' + addition_end_date + '\n')

    # Loop through directory
    print('Looping through regions...')
    regions = os.listdir(master_era5_dir)
    for region in regions:
        print('Starting on ' + region + '...')
        # Identify path to record netCDF for specific region
        record_file_name = ''
        for file in os.listdir(os.path.join(master_era5_dir, region)):
            if file.startswith('Qout_era5') and file.endswith(record_end_date + '.nc'):
                record_file_name = file
        if record_file_name == '':
            print('ERROR: Correct record file not found for ' + region + '\n')
            continue
        record_file_path = os.path.join(master_era5_dir, region, record_file_name)
        print('Record file path: ' + record_file_path)

        # Identify path to addition netCDF for specific region
        addition_file_name = ''
        for file in os.listdir(os.path.join(output_dir, region)):
            if file.startswith('Qout_era5') and file.endswith(addition_start_date + 'to' + addition_end_date + '.nc'):
                addition_file_name = file
        if addition_file_name == '':
            print('ERROR: Correct addition file not found for ' + region + '\n')
            continue
        addition_file_path = os.path.join(output_dir, region, addition_file_name)
        print('Addition file-path: ' + addition_file_path)

        # Append the new simulation onto the record netCDF
        append_era5_to_record(record_file_path, addition_file_path)

        # Rename record netCDF to include new ending date
        print('Renaming record netCDF to include updated ending year... ')
        os.rename(record_file_path, record_file_path.replace(record_end_date + '.nc', addition_end_date + '.nc'))

        # Remove addition netCDF since it has already been appended, and remove any temporary m3*.nc files
        print('Deleting ' + addition_file_path + '...')
        os.remove(addition_file_path)
        for file in os.listdir(os.path.join(output_dir, region)):
            if file.startswith('m3'):
                print('Deleting ' + file + '...')
                os.remove(os.path.join(output_dir, region, file))
        print('Successfully appended new ERA-5 to record netCDF for ' + region + '\n')


    # Finish script
    script_end_time = datetime.now()
    print('\nWorkflow Finished! Total Runtime: ' + str(script_end_time - script_start_time))
