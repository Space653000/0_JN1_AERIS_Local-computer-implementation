"""Version 1.0.0; nvh-integration local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('nvh-integration', params)
