"""Version 1.0.0; gcc-phat-tdoa local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('gcc-phat-tdoa', params)
