"""Read-only independent verification of public contract mirrors at frozen SHA."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aeris_runtime.blueprint_compatibility import TARGET, CONTRACT_HASHES, load_contracts


def main():
    import urllib.request
    load_contracts(ROOT)
    for name in CONTRACT_HASHES:
        url = f'https://raw.githubusercontent.com/Space653000/0_JN1_AERIS/{TARGET}/{name}'
        with urllib.request.urlopen(url, timeout=30) as response:
            upstream = response.read()
        local = (ROOT/'config/blueprint'/name).read_bytes().replace(b'\r\n', b'\n')
        if upstream != local:
            raise ValueError(f'pinned Core source mismatch: {name}')
    print('BLUEPRINT_SOURCE=PASS exact frozen commit; no runtime alignment claim')


if __name__ == '__main__': main()
