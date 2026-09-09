"""Version 1.0.0; spectral-analysis local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('spectral-analysis', params)
