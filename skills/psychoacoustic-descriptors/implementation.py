"""Version 1.0.0; psychoacoustic-descriptors local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('psychoacoustic-descriptors', params)
