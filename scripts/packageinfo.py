"""
run this script in a QGIS-only environment to update .env/packageinfo.csv
E.g.:
conda activate qgis_only
python scripts/packageinfo.py --tag=conda
"""
import argparse
import csv
import platform
import site
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import List

from qgis.core import Qgis


def get_package_info():
    """Returns a dictionary of {package_name: version} for the current environment."""
    packages = {}
    user_site = Path(site.getusersitepackages()).resolve()
    for dist in metadata.distributions():
        dist_path = Path(dist.locate_file('')).resolve()
        try:
            dist_path.relative_to(user_site)
            # If no error, it is inside the user site-packages; skip it
            continue
        except ValueError:
            pass

        name = dist.metadata["Name"]
        packages[name] = dist.version
    return packages


HEADER = ['Tag', 'OS', 'Python', 'QGIS', 'Date']


class QGISSetup(object):

    def __init__(self, info: dict):
        assert isinstance(info, dict)
        info = info.copy()
        self.header = dict()
        for v in HEADER:
            if v in info:
                self.header[v] = info.pop(v)
            else:
                self.header[v] = None
        self.packages = info

    def equalHeader(self, other) -> bool:
        assert isinstance(other, QGISSetup)
        for k in HEADER:
            if k == 'Date':
                continue
            if self.header[k] != other.header[k]:
                return False
        return True


def update_package_csv(tag="", filename=None):
    if filename is None:
        filename = Path(__file__).resolve().parents[1] / ".env" / "packageinfo.csv"
    else:
        filename = Path(filename)

    # 1. Identify current environment details
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    QGIS_SETUPS = []
    # 2. Read existing data if the file exists
    rows = []
    if filename.exists():
        with open(filename, mode="r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            n = len(rows[0]) - 1
            for i in range(1, n + 1):
                infos = dict()
                for row in rows:
                    infos[row[0]] = row[i]
                QGIS_SETUPS.append(QGISSetup(infos))

    packages = get_package_info()
    packages['OS'] = platform.system()
    packages['Python'] = platform.python_version()
    packages['QGIS'] = Qgis.version()
    packages['Date'] = current_date
    if tag:
        packages['Tag'] = tag
    thisSetup = QGISSetup(packages)

    QGIS_SETUPS: List[QGISSetup] = [s for s in QGIS_SETUPS if not thisSetup.equalHeader(s)]
    QGIS_SETUPS.append(thisSetup)

    QGIS_SETUPS = sorted(QGIS_SETUPS, key=lambda s: tuple(str(s.header.get(k, "")).lower() for k in HEADER))

    all_packages = set()
    for s in QGIS_SETUPS:
        all_packages.update(s.packages.keys())

    with open(filename, mode="w", newline="", encoding="utf-8") as f:

        csv_writer = csv.writer(f, lineterminator='\n')
        # csv_writer.writerow(['# Packages QGIS installation'])
        # csv_writer.writerow(['# Updated by scripts/packageinfo.py'])
        # csv_writer.writerow([''])

        for h in HEADER:
            row = [h] + [s.header.get(h) for s in QGIS_SETUPS]
            csv_writer.writerow(row)

        for p in sorted(all_packages, key=lambda v: str(v).lower()):
            row = [p] + [s.packages.get(p) for s in QGIS_SETUPS]
            csv_writer.writerow(row)

    print(f"Updated {filename} for Tag: '{tag}', {thisSetup.header}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log package info to CSV.")
    parser.add_argument("--tag", type=str, default="", help="Environment tag")
    parser.add_argument("--file", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()

    update_package_csv(tag=args.tag, filename=args.file)
