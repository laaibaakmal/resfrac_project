from well_service import WellService
from models.well_result import WellResult

class Program:
    def __init__(self):
        # Program Services
        self.well_service: WellService = WellService()

    def parse_data(self) -> WellResult:
        result = self.well_service.parse_dataset()
        return result

# Starting point of project
def main():
    program: Program = Program()
    result: WellResult = program.parse_data()
    print(result.message)

if __name__ == '__main__':
    main()