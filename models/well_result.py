from models.result import Result

class WellResult(Result):
    slope: float
    
    def __init__(self, isSuccess: bool, message: str, slope: int):        
        super().__init__(isSuccess, message)       
        self.slope = slope