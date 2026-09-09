"""Version 1.0.0; local-audio-regression local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('local-audio-regression', params)
