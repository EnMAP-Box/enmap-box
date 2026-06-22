"""
Fixes SpectralProfile fields in a vector layer.
Converts the content of binary SpectralProfile fields from old-style pickle dumps to binary encoded JSON format.
"""
import argparse
import json
import pickle  # nosec: B403 # we need pickle to reconstruct the old data
import sys
from pathlib import Path
from typing import Union, List, Optional

from enmapbox.qgispluginsupport.qps.speclib.core import is_profile_field
from enmapbox.qgispluginsupport.qps.speclib.core.spectralprofile import validateProfileValueDict
from enmapbox.qgispluginsupport.qps.utils import stringFromByteArray
from qgis.PyQt.QtCore import QByteArray
from qgis.core import QgsField, edit
from qgis.core import QgsVectorLayer
from qgis.testing import start_app


def fix_binary_profile_fields(
    path: Union[str, Path],
    fieldnames: Optional[List[str]] = None
):
    path = str(Path(path))
    print(f'Fix profile fields in: {path}')

    lyr = QgsVectorLayer(path)
    if not lyr.isValid():
        raise ValueError(f'Invalid layer: {path}: {lyr.error()}')

    all_fields = lyr.fields().names()
    binary_fields = [f.name() for f in lyr.fields() if f.typeName() == 'Binary']
    print(f'Found {len(binary_fields)} binary fields: {binary_fields}')

    if isinstance(fieldnames, list):
        wrong_names = [n for n in fieldnames if n not in all_fields]
        if len(wrong_names) > 0:
            raise ValueError(f'Invalid field names: {wrong_names}')
        wrong_type = [n for n in fieldnames if n not in binary_fields]
        if len(wrong_type) > 0:
            raise ValueError(f'Fields exist but are not binary fields: {wrong_type}')
        profile_fields = fieldnames
    else:
        profile_fields = [f.name() for f in lyr.fields() if is_profile_field(f)]

    if len(profile_fields) == 0:
        raise ValueError(
            'No spectral profile fields found. '
            'Use --fieldnames explicit definition.')

    with edit(lyr):
        for n in profile_fields:
            i = lyr.fields().lookupField(n)
            field: QgsField = lyr.fields().field(i)
            print(f'Check "{n}" ({field.typeName()})')
            j = 0
            for f in lyr.getFeatures():
                data_old = f.attribute(i)
                if not isinstance(data_old, QByteArray):
                    continue
                data_old: QByteArray
                profile_dict = None
                needs_conversion = False
                try:
                    profile_dict = json.loads(stringFromByteArray(data_old))
                    # everything is fine
                except UnicodeDecodeError:
                    # old-style pickle format.
                    # using pickle is required here to reconstruct the old data
                    profile_dict = pickle.loads(data_old.data())  # nosec 301
                    needs_conversion = True

                success, msg, d = validateProfileValueDict(profile_dict)
                if not success:
                    raise AssertionError(f'{msg}: {profile_dict}')
                elif needs_conversion:
                    # convert data back to proper Byte Array
                    data_new = QByteArray()
                    data_new.append(json.dumps(profile_dict, ensure_ascii=False).encode())
                    lyr.changeAttributeValue(f.id(), i, data_new, data_old)
                    j += 1

            print(f'Fixed {j} profile(s) in field {field.name()}')

    del lyr


def main():
    parser = argparse.ArgumentParser(
        description="Fix binary profile fields in vector layers"
    )

    # Path argument: can accept strings, handles Path transformations internally
    parser.add_argument(
        "path",
        type=str,
        help="Path to the vector layer file (e.g., GeoPackage, Shapefile, etc.)"
    )

    parser.add_argument('-f', '--fieldnames',
                        nargs='+',
                        default=None, help='List of field names to fix')

    args = parser.parse_args()

    # Verify path exists before starting QGIS overhead
    input_path = Path(args.path)
    if not input_path.exists():
        print(f"Error: The file path '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print("Initializing QGIS Application...")

    start_app()
    # Run your processing function
    fix_binary_profile_fields(input_path, fieldnames=args.fieldnames)


if __name__ == "__main__":
    main()
