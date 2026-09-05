"""Version 1.0.0; thermal-rc local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('thermal-rc', params)
