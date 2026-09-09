"""Version 1.0.0; lumped-speaker local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('lumped-speaker', params)
