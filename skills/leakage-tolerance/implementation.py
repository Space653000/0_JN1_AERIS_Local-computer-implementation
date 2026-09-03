"""Version 1.0.0; leakage-tolerance local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('leakage-tolerance', params)
