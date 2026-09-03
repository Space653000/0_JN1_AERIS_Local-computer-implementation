"""Version 1.0.0; porous-absorption local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('porous-absorption', params)
