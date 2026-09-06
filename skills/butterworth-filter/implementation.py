"""Version 1.0.0; butterworth-filter local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('butterworth-filter', params)
