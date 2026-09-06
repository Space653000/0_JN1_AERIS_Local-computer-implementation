"""Version 1.0.0; provenance-research local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('provenance-research', params)
