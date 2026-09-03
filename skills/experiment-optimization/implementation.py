"""Version 1.0.0; experiment-optimization local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('experiment-optimization', params)
