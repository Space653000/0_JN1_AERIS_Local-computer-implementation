"""Version 1.0.0; requirement-traceability local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('requirement-traceability', params)
