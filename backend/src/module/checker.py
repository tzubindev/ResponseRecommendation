import pandas as pd

class Checker:
    def __init__(self, file_path):
        self.df = pd.read_csv(file_path, header=0)

    def has_data(self):
        if not self.df.empty:
            return True
        else:
            return False
