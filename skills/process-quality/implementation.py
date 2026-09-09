"""Version 1.0.0; process-quality local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('process-quality', params)
