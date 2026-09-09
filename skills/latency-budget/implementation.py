"""Version 1.0.0; latency-budget local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('latency-budget', params)
