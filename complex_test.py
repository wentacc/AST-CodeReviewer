import os
import sys

# Top level constant
MAX_RETRIES = 5

def top_level_function(x):
    """A top level function."""
    return x * 2

class DataProcessor:
    """A class to process data."""
    def __init__(self, data):
        self.data = data

    def process(self):
        """Process the data."""
        results = []
        for item in self.data:
            results.append(item * 2)
        return results

class NetworkManager:
    """A class to manage network."""
    def connect(self, url):
        print(f"Connecting to {url}")

    def disconnect(self):
        print("Disconnecting")

def another_function():
    print("Another one")
