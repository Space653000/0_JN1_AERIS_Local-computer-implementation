"""Version 1.0.0; instrument-sequence local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('instrument-sequence', params)
