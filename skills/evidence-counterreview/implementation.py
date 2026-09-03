"""Version 1.0.0; evidence-counterreview local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('evidence-counterreview', params)
