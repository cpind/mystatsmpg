import os

def _filepath(filename):
    return os.path.join(os.path.dirname(__file__), "../../" + filename)
