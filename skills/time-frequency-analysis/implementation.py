"""Version 1.0.0; time-frequency-analysis local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('time-frequency-analysis', params)
