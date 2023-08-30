import csv

class CSVHandler:
    def __init__(self, filename: str):
        self.data = []
        with open(filename, mode='r') as csvfile:
            for row in csv.DictReader(csvfile):
                self.data.append(row)

