"""Version 1.0.0; level-statistics local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('level-statistics', params)
