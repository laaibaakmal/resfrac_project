ResFrac Project
This project processes well pressure data from a CSV file and outputs three CSV files with observed, detrended, and trend pressure data. 
It also plots our processed data.

INSTRUCTIONS TO CLONE
```git clone https://github.com/laaibaakmal/resfrac_project.git```

Project Structure
There is a visual system diagram in the 'assets/' folder called 'system_diagram.png'
I generated this project tree from: https://woochanleee.github.io/project-tree-generator/
RESFRAC_PROJECT/
│
├── data/
│   └── dataset.csv             # Input CSV file with well pressure data
├── logs/
│   └── errors.log              # Log file for errors encountered during processing
├── models/
│   ├── config.py               # Config class handling configuration settings and inputs
│   ├── result.py               # Result class
│   └── well_result.py          # WellResult class to return the result of the processing
├── output/
│   ├── detrended_data.csv      # Output file with detrended data
│   ├── observed_data.csv       # Output file with filtered data
│   └── trend_data.csv          # Output file with trend data
├── config.json                 # Configuration file for setting up input parameters and file locations
├── program.py                  # Main program entry point
├── readme.txt                  # Project documentation
├── well_service.py             # Main service that processes well data

Prerequisites
To run the program, you will need to have the following installed:

Python 3.x (Developed using version 3.11.3)
Required Python packages:
pandas
numpy
matplotlib
scipy
json
logging

You can install the required dependencies using:
pip install -r requirements.txt

Configuration
The program uses a configuration file, config.json, to manage input and output settings. 
You can customize the file paths, CSV file names, and the well processing options by editing the config.json file as needed.
This file contains the following structure:
{
  "Settings": {
    "data_folder": "data/",
    "data_file": "dataset.csv",
    "output_folder": "output/",
    "observed_filename": "observed_data.csv",
    "detrended_filename": "detrended_data.csv",
    "trend_filename": "trend_data.csv"
  },
  "Inputs": {
    "well_name": "Well_4A",
    "start_time": "600",
    "end_time": "624",
    "slope": -2,
    "use_estimated_slope": true
  }
}

Settings:
data_folder: Folder containing the input CSV file.
data_file: Name of the input CSV file.
output_folder: Folder where the output CSV files will be saved.
observed_filename: Filename for the observed data CSV file.
detrended_filename: Filename for the detrended data CSV file.
trend_filename: Filename for the trend data CSV file.

Inputs:
well_name: The name of the well to process.
start_time: Start time for detrending the pressure data.
end_time: End time for detrending the pressure data.
slope: Manual slope value for detrending. Ignored if use_estimated_slope is set to true.
use_estimated_slope: If true, the program will estimate the slope from pre-test data.

Running the Program
Place your input CSV file in the data/ folder and adjust the configuration in the config.json file.

Run the program:
python program.py

The program will process the CSV data and generate three output CSV files in the output/ folder:
observed_data.csv: The filtered pressure data.
detrended_data.csv: The detrended pressure data.
trend_data.csv: The trend pressure data.

After processing, the program will also plot the observed, trend, and detrended data for visualization.

Logging
Any errors encountered during the processing are logged in the logs/errors.log file. 
You can check this file for more information if the program encounters issues.
