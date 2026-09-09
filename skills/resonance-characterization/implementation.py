"""Version 1.0.0; resonance-characterization local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('resonance-characterization', params)
