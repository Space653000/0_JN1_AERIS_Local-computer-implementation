"""Version 1.0.0; circuit-noise-budget local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('circuit-noise-budget', params)
