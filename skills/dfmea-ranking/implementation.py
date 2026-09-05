"""Version 1.0.0; dfmea-ranking local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('dfmea-ranking', params)
