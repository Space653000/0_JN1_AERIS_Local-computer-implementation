"""Version 1.0.0; uncertainty-propagation local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('uncertainty-propagation', params)
