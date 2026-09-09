"""Version 1.0.0; failure-hypotheses local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('failure-hypotheses', params)
