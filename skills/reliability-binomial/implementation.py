"""Version 1.0.0; reliability-binomial local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('reliability-binomial', params)
