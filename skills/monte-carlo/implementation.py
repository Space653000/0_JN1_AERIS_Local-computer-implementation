"""Version 1.0.0; monte-carlo local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('monte-carlo', params)
