"""Version 1.0.0; enhancement-aec-metrics local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('enhancement-aec-metrics', params)
