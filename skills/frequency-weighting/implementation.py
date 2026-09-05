"""Version 1.0.0; frequency-weighting local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('frequency-weighting', params)
