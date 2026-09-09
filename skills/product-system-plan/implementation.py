"""Version 1.0.0; product-system-plan local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('product-system-plan', params)
