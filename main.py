import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

input_data_folder = "data/"
output_folder = "output/"

def main():
    try:
        # I can read the inputs from testinfo.txt, but prompting
        # the user to enter the data in the console is convenient.
        well_name = input("Enter the well name (ex: Well_11A): ")
        start_time = float(input("Enter the start time (ex: 590): "))
        end_time = float(input("Enter the end time (ex: 624): "))
        # slope = float(input("Enter the slope (ex: -1.5): "))

        # Read CSV data
        csv_file = input_data_folder + 'dataset.csv'
        well_data = read_csv_data(csv_file, well_name)

        if well_data is None:
            return None

        # Ask the user if they want to enter the slope manually or estimate it
        use_estimated_slope = input("Do you want to estimate the slope automatically? (y/n): ").lower()
        
        if use_estimated_slope == 'y':
            slope = estimate_slope(well_data, start_time)
            print(f"Estimated slope: {slope}")
        else:
            slope = float(input("Enter the slope (ex: -1.5): "))

        # Smooth out pressure data (filter out points with < 0.5 psi differences)
        filtered_data = filter_pressure_data(well_data)
        
        if filtered_data is None:
            return None

        # Detrend data based on the given slope
        detrended_data, trend_data = detrend_data(filtered_data, start_time, end_time, slope)
        
        if detrended_data is None or trend_data is None:
            return None

        # Save output to CSV files
        save_output(filtered_data, detrended_data, trend_data)

        # Plot the data from 24 hours before the start_time to the end_time
        plot_data(start_time, end_time)
    except ValueError as e:
        print(e)
        return None
    except KeyError as e:
        print(e)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Function to estimate the slope from pre-test data
def estimate_slope(well_data, start_time):
    # Use the data before the start time to estimate the slope
    pre_test_data = well_data[well_data['Time'] < start_time]
    
    # Ensure there's enough data to estimate the slope
    if pre_test_data.empty:
        raise ValueError("Not enough data before the start time to estimate slope.")
    
    # Linear regression to estimate slope (y = mx + b, we extract 'm')
    slope, _ = np.polyfit(pre_test_data['Time'], pre_test_data['Pressure'], 1)
    
    return slope

# Read the input well's time and pressure data from the CSV
def read_csv_data(csv_file, well_name):
    try:
        # Set our header rows and skip the rows that contain unnecessary metadata
        df_pressure = pd.read_csv(csv_file, header=1, skiprows=[2, 3])
        df_time = pd.read_csv(csv_file, header=2, skiprows=[3])

        # Check if our input well_name exists in the DataFrame columns
        if well_name not in df_pressure.columns:
            raise ValueError(f"Well name '{well_name}' does not exist in the CSV file.")

        pressure_data = df_pressure[well_name]
        time_data = df_time['Time']
        
        # Create a single new DataFrame with Time and Pressure columns
        well_data = pd.DataFrame({
            'Time': time_data,
            'Pressure': pressure_data
        })

        return well_data
    
    except ValueError as e:
        print(e)
        return None
    except KeyError as e:
        print(f"Error: {e}. Make sure the CSV file contains the required columns.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    
def filter_pressure_data(well_data):
    try:
        # Lets check if the 'Pressure' column exists in well_data
        if 'Pressure' not in well_data.columns:
            raise KeyError("'Pressure' column is missing from the well data.")

        # Make sure the 'Pressure' column contains numeric data only
        if not pd.api.types.is_numeric_dtype(well_data['Pressure']):
            raise ValueError("'Pressure' column contains non-numeric data.")

        # Calculate pressure differences only for the 'Pressure' column
        pressure_diff = well_data['Pressure'].diff().abs()

        # Filter the data based on the pressure difference being >= 0.5
        filtered_data = well_data[pressure_diff >= 0.5].copy().dropna()

        # Ensure filtered data isn't empty
        if filtered_data.empty:
            raise ValueError("No data points meet the filtering criteria (pressure difference >= 0.5).")
        
        return filtered_data

    except KeyError as e:
        print(f"Error: {e}")
        return None
    except ValueError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def detrend_data(well_data, start_time, end_time, slope):
    # Ensure Time is a float
    well_data['Time'] = well_data['Time'].astype(float)

    # Calculate the trend starting from 24 hours before start_time
    start_time_window = start_time - 24

    # Create a linear trend based on the provided slope
    # Find the closest Time to start_time
    closest_start_time_idx = (well_data['Time'] - start_time).abs().idxmin()
    
    # Find the closest pressure at the start_time for detrending
    start_pressure = well_data.loc[closest_start_time_idx, 'Pressure']

    # Generate time points for the extended trend (24 hours before start_time to end_time)
    # I'll create 100 points for the trend line
    extended_time = pd.Series(np.linspace(start_time_window, end_time, num=100))  

    # Calculate the trend pressure for this extended time window [based on a y=mx+b linear trend]
    trend_pressure = start_pressure + slope * (extended_time - start_time)  

    # Append the trend line to the well_data DataFrame
    trend_data = pd.DataFrame({
        'Time': extended_time,
        'Trend Pressure': trend_pressure
    })

    # Calculate detrended pressure for observed data within the original time range
    well_data['Trend Pressure'] = start_pressure + slope * (well_data['Time'] - start_time)
    well_data['Detrended Pressure'] = well_data['Pressure'] - well_data['Trend Pressure']
    
    # Filter data between start_time and end_time for output
    detrended_data = well_data[(well_data['Time'] >= start_time) & (well_data['Time'] <= end_time)].copy()
    return detrended_data, trend_data

def save_output(filtered_data, detrended_data, trend_data):
    # Save filtered data and detrended data to CSV files
    filtered_data.to_csv(output_folder + 'filtered_pressure_data.csv', index=False)
    detrended_data.to_csv(output_folder + 'detrended_pressure_data.csv', index=False)
    trend_data.to_csv(output_folder + 'trend_pressure_data.csv', index=False)  # Save the trend data
    print("Data saved to 'filtered_pressure_data.csv', 'detrended_pressure_data.csv', and 'trend_pressure_data.csv'")

def plot_data(start_time, end_time):
    # Load the saved P-vs-T CSVs
    # Observed data starting 24 hrs before start_time:
    filtered_data = pd.read_csv(output_folder + 'filtered_pressure_data.csv')
    
    # Calculated detrended data, between the start and end time of the test:
    detrended_data = pd.read_csv(output_folder + 'detrended_pressure_data.csv')
    
    # Linear trend-calculated data, between test start & end times:
    trend_data = pd.read_csv(output_folder + 'trend_pressure_data.csv')  # Load the extended trend data
    
    # Define the time window: 24 hours before start_time and up to end_time
    start_time_window = start_time - 24

    # Filter the data to include only the time window from 24 hours before start_time to end_time
    filtered_data = filtered_data[(filtered_data['Time'] >= start_time_window) & (filtered_data['Time'] <= end_time)]
    detrended_data = detrended_data[(detrended_data['Time'] >= start_time_window) & (detrended_data['Time'] <= end_time)]
    trend_data = trend_data[(trend_data['Time'] >= start_time_window) & (trend_data['Time'] <= end_time)]

    # Plot observed pressure, trend pressure, and detrended pressure
    plt.figure(figsize=(10, 6))

    # Plot filtered observed pressure
    plt.scatter(filtered_data['Time'], filtered_data['Pressure'], label='Observed Pressure', color='blue')

    # Plot extended trend pressure line (including 24 hours before start_time)
    plt.plot(trend_data['Time'], trend_data['Trend Pressure'], label='Extended Trend Pressure', linestyle='--', color='green')

    # Plot detrended pressure
    # plt.plot(detrended_data['Time'], detrended_data['Detrended Pressure'], label='Detrended Pressure', linestyle='-.', color='red')

    # Adding labels and title
    plt.title('Pressure vs Time (including extended trend pressure)')
    plt.xlabel('Time (hours)')
    plt.ylabel('Pressure (psi)')
    plt.legend()

    # Show the plot
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()




#import

# import pandas as pd

# #user enters info
# def main():

#     try:  
#         well_name = input("Enter Well Name: ")
#         start_time = float(input("Enter Start Time (hours): "))
#         end_time = float(input("Enter End Time (hours): "))
#         slope = float(input("Enter Slope (psi/hours): "))

#         well_data = read_csv_data(well_name)
#         if well_data is None:
#             return None
#         #print(csv_data['Time'])

#         filtered_data = filter_pressure_data(well_data)
#         if filtered_data is None:
#             return None

#     except ValueError as e: 
#         print(e)
#         return None
#     except KeyError as e: 
#         print(e)
#         return None
#     except Exception as e: 
#         print(e)
#         return None

# # Write your code here
# def read_csv_data(well_name):
#     try:
#         csv_file_path = 'data/dataset.csv'
#         # Set our header rows and skip the rows that contain unnecessary metadata
#         df_pressure = pd.read_csv(csv_file_path, header=1, skiprows=[2, 3])
#         df_time = pd.read_csv(csv_file_path, header=2, skiprows=[3])

#         # Check if our input well_name exists in the DataFrame columns
#         if well_name not in df_pressure.columns:
#             raise ValueError(f"Well name '{well_name}' does not exist in the CSV file.")

#         pressure_data = df_pressure[well_name]
#         time_data = df_time['Time']
        
#         # Create a single new DataFrame with Time and Pressure columns
#         well_data = pd.DataFrame({
#             'Time': time_data,
#             'Pressure': pressure_data
#         })
#         print(well_data)

#         return well_data
    
#     except ValueError as e:
#         print(e)
#         return None
#     except KeyError as e:
#         print(f"Error: {e}. Make sure the CSV file contains the required columns.")
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         return None

# def filter_pressure_data(well_data):
#     try:
#         pressure_diff = well_data['Pressure'].diff().abs()
#         filtered_data =  well_data[pressure_diff >= 0.5].copy().dropna() 
#         if filtered_data.empty:
#             raise ValueError('No data points.')
#         print(pressure_diff)
#         return filtered_data

#     except ValueError as e:
#         print(e)
#         return None
#     except KeyError as e:
#         print(e)
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         return None      
    
# def detrend_data():
#     try:
#     # y= mx+b
#     # trend pressure = (input slope)*( time - start time) + start pressure
    
#     except ValueError as e:
#         print(e)
#         return None
#     except KeyError as e:
#         print(e)
#         return None
#     # except Exception as e:
#     #     print(f"An unexpected error occurred: {e}")
#     #     return None


# if __name__ == "__main__":
#     main()


