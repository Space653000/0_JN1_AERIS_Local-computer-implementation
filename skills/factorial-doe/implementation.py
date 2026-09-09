"""Version 1.0.0; factorial-doe local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('factorial-doe', params)
