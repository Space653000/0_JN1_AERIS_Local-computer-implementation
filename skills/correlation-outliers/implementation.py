"""Version 1.0.0; correlation-outliers local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('correlation-outliers', params)
