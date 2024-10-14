from typing import Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import logging
from scipy.stats import linregress
from models.config import Config
from models.well_result import WellResult

class WellService:

    def __init__(self):
        # Load our config file
        config_file_path = "config.json"
        with open(config_file_path, "r") as config_file:
            config_data = json.load(config_file)

        # Instantiate the Config class with the data from JSON
        self.app_config: Config = Config(config_data['Settings'], config_data['Inputs'])
        
        # Configure logger output
        logging.basicConfig(filename='logs/errors.log', level=logging.ERROR)
    
    def parse_dataset(self) -> WellResult:
        """
        Starting point for processing pressure data when monitoring 
        downward pressure response in the monitoring well.

        Returns:
            WellResult: Returns WellResult object with details about the result.
        """
        try:
            app_config = self.app_config

            well_name = app_config.well_name
            start_time = float(app_config.start_time)
            end_time = float(app_config.end_time)

            # Read CSV data
            csv_file_path = app_config.data_folder + app_config.data_file
            well_data = self.read_csv_data(csv_file_path, well_name)

            if well_data is None:
                return WellResult(False, 'Error: Check errors.log for more info.', None)
            
            # Check if they want to  the slope manually or estimate it
            if app_config.use_estimated_slope == True:
                slope = self.estimate_slope(well_data, start_time)
            else:
                slope = float(app_config.slope)

            # Smooth out pressure data (filter out points with < 0.5 psi differences)
            filtered_data = self.filter_pressure_data(well_data)

            if filtered_data is None:
                return WellResult(False, 'Error: Check errors.log for more info.', slope)

            # Detrend data based on the slope
            detrended_data, trend_data = self.detrend_data(filtered_data, start_time, end_time, slope)
            
            if detrended_data is None or trend_data is None:
                return WellResult(False, 'Error: Check errors.log for more info.', slope)

            # Save output to CSV files
            self.save_output(filtered_data, detrended_data, trend_data, start_time, end_time)

            # Plot the data from 24 hours before the start_time to the end_time
            self.plot_data(start_time, end_time, slope)
            
            return WellResult(True, f"Success! Check '{app_config.output_folder}' for CSVs.", slope)

        except ValueError as e:
            logging.error(e, exc_info=True)
            return WellResult(False, "Value Error: Check errors.log file for more info.", None)
        except KeyError as e:
            logging.error(e, exc_info=True)
            return WellResult(False, "Key Error: Check errors.log file for more info.", None)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)
            return WellResult(False, "Exception: Check errors.log file for more info.", None)


    def read_csv_data(self, csv_file_path: str, well_name: str) -> pd.DataFrame:
        """
        Reads the well's time and pressure data from the CSV file.

        Args:
            csv_file_path (str): Path to the CSV file.
            well_name (str): The well name to look for in the CSV columns.

        Returns:
            pd.DataFrame: DataFrame containing Time and Pressure columns.
            None: If the well name does not exist in the CSV or an error occurs.
        """
        try:
            df_pressure = pd.read_csv(csv_file_path, header=1, skiprows=[2, 3])
            df_time = pd.read_csv(csv_file_path, header=2, skiprows=[3])

            if well_name not in df_pressure.columns:
                raise ValueError(f"Well name '{well_name}' does not exist in the CSV file.")
                                        
            pressure_data = df_pressure[well_name]
            time_data = df_time['Time']

            well_data = pd.DataFrame({
                'Time': time_data,
                'Pressure': pressure_data
            })

            return well_data
        
        except ValueError as e:
            logging.error(e, exc_info=True)
            return None
        except KeyError as e:
            logging.error(f"Error: {e}. Make sure the CSV file contains the required columns.", exc_info=True)
            return None
        except Exception as e:
            logging.error(e, exc_info=True)
            return None


    def estimate_slope(self, well_data: pd.DataFrame, start_time: float) -> float:
        """
        Estimates the slope from the well's pre-test data using linear regression.

        Args:
            well_data (pd.DataFrame): DataFrame containing well data.
            start_time (float): The start time for the test.

        Returns:
            float: Estimated slope of the linear trend.
        
        Raises:
            ValueError: If there are not enough data points to estimate the slope.
        """
        try:
            lower_time_limit = start_time - 24
            pre_test_data = well_data[(well_data['Time'] >= lower_time_limit) & (well_data['Time'] < start_time)].dropna(subset=['Time', 'Pressure'])

            if len(pre_test_data) < 2:
                raise ValueError("Not enough data points to estimate slope. At least two points are required.")

            time_data = pre_test_data['Time']
            pressure_data = pre_test_data['Pressure']

            # linregress outputs: slope, intercept, r_value, p_value, std_err 
            slope, _, _, _, _ = linregress(time_data, pressure_data)

            print(f"Estimated slope: {slope}")
            return slope
        
        except KeyError as e:
            logging.error(e, exc_info=True)
            return None
        except ValueError as e:
            logging.error(e, exc_info=True)
            return None
        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    def filter_pressure_data(self, well_data: pd.DataFrame) -> pd.DataFrame:
        """
        Filters out pressure data points with differences less than 0.5 psi.

        Args:
            well_data (pd.DataFrame): DataFrame containing well data.

        Returns:
            pd.DataFrame: DataFrame with filtered pressures and time.
            None: If no data meets the filtering criteria or an error occurs.
        """
        try:
            if 'Pressure' not in well_data.columns:
                raise KeyError("'Pressure' column is missing from the well data.")

            if not pd.api.types.is_numeric_dtype(well_data['Pressure']):
                raise ValueError("'Pressure' column contains non-numeric data.")

            # O(n) time-complexity two pointer filtering:
            filtered_pressures = []
            filtered_time = []
            i = 0
            while i < len(well_data['Pressure']):
                pressure = well_data['Pressure'][i]
                j = i
                while j + 1 < len(well_data['Pressure']) and abs(well_data['Pressure'][j+1] - pressure) < 0.5:
                    j += 1
                filtered_pressures.append(pressure)
                filtered_time.append(well_data['Time'][i])
                i = j + 1

            filtered_data = pd.DataFrame({
                'Pressure': filtered_pressures,
                'Time': filtered_time
            })
            
            filtered_data = filtered_data.dropna(subset=['Time', 'Pressure'])
            
            if filtered_data['Pressure'].empty:
                raise ValueError("No data points meet the filtering criteria (pressure difference >= 0.5).")
            
            return filtered_data

        except KeyError as e:
            logging.error(e, exc_info=True)
            return None
        except ValueError as e:
            logging.error(e, exc_info=True)
            return None
        except Exception as e:
            logging.error(e, exc_info=True)
            return None


    def detrend_data(self, well_data: pd.DataFrame, start_time: float, end_time: float, slope: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Detrends the well data based on the provided slope.

        Args:
            well_data (pd.DataFrame): DataFrame containing well data.
            start_time (float): The start time for detrending.
            end_time (float): The end time for detrending.
            slope (float): The slope to detrend the data.

        Returns:
            pd.DataFrame: Detrended data.
            pd.DataFrame: Trend data.
        """
        try:
            well_data['Time'] = well_data['Time'].astype(float)

            start_time_window = start_time - 24
            closest_start_time_idx = (well_data['Time'] - start_time).abs().idxmin()
            start_pressure = well_data.loc[closest_start_time_idx, 'Pressure']

            extended_time = pd.Series(np.linspace(start_time_window, end_time, num=100))  
            trend_pressure = start_pressure + slope * (extended_time - start_time)  

            trend_data = pd.DataFrame({
                'Time': extended_time,
                'Trend Pressure': trend_pressure
            })

            well_data['Trend Pressure'] = start_pressure + slope * (well_data['Time'] - start_time)
            detrended_data = pd.DataFrame({
                'Time': well_data['Time'],
                'Detrended Pressure': well_data['Pressure'] - well_data['Trend Pressure']
            })
            
            detrended_data = detrended_data[(detrended_data['Time'] >= start_time) & (detrended_data['Time'] <= end_time)]

            return detrended_data, trend_data

        except KeyError as e:
            logging.error(e, exc_info=True)
            return None
        except ValueError as e:
            logging.error(e, exc_info=True)
            return None
        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    def save_output(self, filtered_data: pd.DataFrame, detrended_data: pd.DataFrame, trend_data: pd.DataFrame, start_time: float, end_time: float):
        """
        Saves filtered, detrended, and trend data to CSV files.

        Args:
            filtered_data (pd.DataFrame): DataFrame with filtered data.
            detrended_data (pd.DataFrame): DataFrame with detrended data.
            trend_data (pd.DataFrame): DataFrame with trend data.
            start_time (float): The start time of the test.
            end_time (float): The end time of the test.
        """
        try:
            pre_start_time = start_time - 24
            observed_data = filtered_data[(filtered_data['Time'] >= pre_start_time) & (filtered_data['Time'] <= end_time)]
            observed_data = pd.DataFrame({
                'Time': observed_data['Time'],
                'Pressure': observed_data['Pressure']
            })

            app_config = self.app_config
            observed_data.to_csv(app_config.output_folder + app_config.observed_filename, index=False)
            detrended_data.to_csv(app_config.output_folder + app_config.detrended_filename, index=False)
            trend_data.to_csv(app_config.output_folder + app_config.trend_filename, index=False)
            print(f"Data saved to '{app_config.observed_filename}', '{app_config.detrended_filename}', and '{app_config.trend_filename}'")

        except KeyError as e:
            logging.error(e, exc_info=True)
            return None
        except ValueError as e:
            logging.error(e, exc_info=True)
            return None
        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    def plot_data(self, start_time: float, end_time: float, slope: float):
        """
        Plots the observed pressure, trend pressure, and detrended pressure against time.

        Args:
            start_time (float): The start time for plotting.
            end_time (float): The end time for plotting.
        """
        try:
            app_config = self.app_config
            filtered_data = pd.read_csv(app_config.output_folder + app_config.observed_filename)
            detrended_data = pd.read_csv(app_config.output_folder + app_config.detrended_filename)
            trend_data = pd.read_csv(app_config.output_folder + app_config.trend_filename)
            
            start_time_window = start_time - 24

            filtered_data = filtered_data[(filtered_data['Time'] >= start_time_window) & (filtered_data['Time'] <= end_time)]
            detrended_data = detrended_data[(detrended_data['Time'] >= start_time_window) & (detrended_data['Time'] <= end_time)]
            trend_data = trend_data[(trend_data['Time'] >= start_time_window) & (trend_data['Time'] <= end_time)]

            plt.rcParams.update({'font.size': 14})
            plt.figure(figsize=(10, 6))

            plt.scatter(filtered_data['Time'], filtered_data['Pressure'], label='Observed Pressure', color='blue')
            plt.plot(trend_data['Time'], trend_data['Trend Pressure'], label=f"Pre-interference linear trend [m={round(slope,2)}]", linestyle='--', color='orange')
            plt.axvline(x=start_time, color='black', linestyle='-', label='Start Time')
            plt.plot(detrended_data['Time'], detrended_data['Detrended Pressure'], label='Detrended Pressure', linestyle='-.', color='red')

            plt.title('Well Pressure Observation vs Time')
            plt.xlabel('Time (Hours)', fontsize=16)
            plt.ylabel('Monitoring well BHP (psi)', fontsize=16)
            plt.legend(loc='lower left')
            plt.grid(True)
            plt.show()

        except KeyError as e:
            logging.error(e, exc_info=True)
            return None
        except ValueError as e:
            logging.error(e, exc_info=True)
            return None
        except Exception as e:
            logging.error(e, exc_info=True)
            return None        