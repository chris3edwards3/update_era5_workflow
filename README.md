# OLD VERSION, Updated version is on BYU-Hydroinformatics

# Update ERA-5 Workflow

The purpose of this workflow is to continuously update the ERA-5 RAPID simulation as new ERA-5 Runoff data becomes available. The ERA-5 Historical Simulation is part of the GEOGloWS Streamflow Services.

## Required Setup

1. Install RAPID and RAPIDpy. The version of RAPIDpy should come from https://github.com/BYU-Hydroinformatics/RAPIDpy because it can process the ERA-5 grid.
2. Create a rapid-io directory that has an input and output folder. The input folder should have a sub-folder for every region that contains the required RAPID input files and the ERA-5 weight table (weight_era_t640.csv).
3. The input folder for each region needs to have an initial flows file from the last ERA-5 simulation (eg: "qinit_era5_t640_24hr_19790101to20181231.csv"). The filename must start with "qinit_era5" and end with "YYYYMMDDtoYYYYMMDD.csv".
4. RAPID needs access to a folder with the ERA-5 gridded runoff data from ECMWF. This data is normally stored in daily netcdf files.
5. Create a directory for log files. In that directory, create a file called "last_date_prev_sim.txt". In that file put the last date of the most recent ERA-5 simulation in format YYYYMMDD (eg: 20181231). This date should match the ending date in the initial flows file exactly.
6. Create a directory for the record files. This directory will annual ERA-5 simulation record files for each region.
7. Required python packages in addition to RAPIDpy: netCDF4 & numpy

## Workflow description
1. The script reads the last simulation date from a text file. It then determines what the starting date should be.
2. For each region, when the RAPID process is launched, it looks for an initial flows file that matches the date from the text file.
3. RAPID is run for each region, with the starting flows from the init file. At the end of the RAPID simulatino, a new init file is created for the next run.
4. The script identifies the actual end date of the simulation from the output Qout filename. 
5. For each region, the recently completed simulation is appended to the record file for that year. If it is the first simulation in a year, a new record file is created from the Qout file.
6. A new text file is created with the last date of the completed simulation. This tells the next simulation when to start.

## Running the script.

To run the workflow, execute the update_era5_workflow.py script from the command line. This script expects 5 more arguments:
1. Path to rapid executable
2. Path to folder with ERA-5 gridded runoff netcdf files
3. Path to master rapid-io directory that contains the input and output folders
4. Path to directory of log files
5. Path to directory of record files

For Example: 
```bash
python update_era5_workflow.py /home/rapid/run/rapid /mnt/ERA5_Runoff /home/rapid-io /home/logs /home/era5_records
```

Lastly, the scripts need to be in a place where they can access the RAPIDpy code (see imports_era5_workflow.py). 
