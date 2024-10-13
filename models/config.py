class Config:
    # file settings related config
    data_folder: str
    data_file: str
    output_folder: str
    observed_filename: str
    detrended_filename: str
    trend_filename: str
    # user input related config
    well_name: str
    start_time: str
    end_time: str
    slope: float
    use_estimated_slope: bool

    def __init__(self, settings, inputs):
        # Settings
        self.data_folder = settings['data_folder']
        self.data_file = settings['data_file']
        self.output_folder = settings['output_folder']
        self.observed_filename = settings['observed_filename']
        self.detrended_filename = settings['detrended_filename']
        self.trend_filename = settings['trend_filename']
        
        # Inputs
        self.well_name = inputs['well_name']
        self.start_time = inputs['start_time']
        self.end_time = inputs['end_time']
        self.slope = inputs['slope']
        self.use_estimated_slope = inputs['use_estimated_slope']

    def __repr__(self):
        return (f"Config(data_folder={self.data_folder}, data_file={self.data_file}, "
                f"output_folder={self.output_folder}, observed_filename={self.observed_filename}, "
                f"detrended_filename={self.detrended_filename}, trend_filename={self.trend_filename}, "
                f"well_name={self.well_name}, start_time={self.start_time}, end_time={self.end_time}, "
                f"slope={self.slope}, use_estimated_slope={self.use_estimated_slope})")