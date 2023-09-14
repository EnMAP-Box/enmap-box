import re
from collections import OrderedDict
from typing import Dict, Any

from enmapbox.typeguard import typechecked


@typechecked
class EnviUtils(object):

    @staticmethod
    def readEnviHeader(filename: str) -> Dict[str, Any]:
        # simplified version of qps.speclib.io.envi.readENVIHeader (also fixes issue #622)
        with open(filename, encoding='utf-8') as file:
            hdr = file.readlines()

        i = 0
        while i < len(hdr):
            if '{' in hdr[i]:
                while '}' not in hdr[i]:
                    hdr[i] = hdr[i] + hdr.pop(i + 1)
            i += 1

        hdr = [''.join(re.split('\n[ ]*', line)).strip() for line in hdr]
        # keep lines with <tag>=<value> structure only
        hdr = [line for line in hdr if re.search(r'^[^=]+=', line)]

        # restructure into dictionary of type
        # md[key] = single value or
        # md[key] = [list-of-values]
        md = OrderedDict()
        for line in hdr:
            tmp = line.split('=')
            key, value = tmp[0].strip(), '='.join(tmp[1:]).strip()
            if value.startswith('{') and value.endswith('}'):
                value = [v.strip() for v in value.strip('{}').split(',')]
                if len(value) > 0 and len(value[0]) > 0:
                    md[key] = value
            else:
                if len(value) > 0:
                    md[key] = value

        return md
