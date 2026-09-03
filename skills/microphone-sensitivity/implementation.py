"""Version 1.0.0; microphone-sensitivity local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('microphone-sensitivity', params)
