"""Version 1.0.0; room-ir-decay local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('room-ir-decay', params)
