"""Version 1.0.0; engineering-requirements local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('engineering-requirements', params)
