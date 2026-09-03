"""Version 1.0.0; repeatability-reproducibility local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('repeatability-reproducibility', params)
