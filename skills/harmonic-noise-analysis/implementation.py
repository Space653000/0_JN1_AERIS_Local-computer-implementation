"""Version 1.0.0; harmonic-noise-analysis local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('harmonic-noise-analysis', params)
