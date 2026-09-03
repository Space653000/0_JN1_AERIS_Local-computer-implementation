"""Version 1.0.0; transfer-coherence local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('transfer-coherence', params)
