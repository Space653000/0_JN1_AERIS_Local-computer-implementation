"""Version 1.0.0; response-phase-delay local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('response-phase-delay', params)
