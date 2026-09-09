"""Version 1.0.0; delay-sum-beamforming local entrypoint."""
from aeris_runtime.engineering.catalog import execute

def run(params):
    return execute('delay-sum-beamforming', params)
