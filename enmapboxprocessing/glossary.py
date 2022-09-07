import re
import warnings
from os.path import join, abspath
from typing import List

filename = abspath(join(__file__, '../glossary.rst'))
baselink = 'https://enmap-box.readthedocs.io/en/latest/general/glossary.html'

# parse glossary from glossary.rst
glossary = dict()
try:
    with open(filename) as file:
        for line in file.readlines():
            if line[:4] == '    ' and line[4] not in ' .:':
                line = line.strip()
                glossary[
                    line] = f'{baselink}#term-{line.replace(" ", "-").lower()}'  # term-* anchor needs to be lower case
                glossary[line + 's'] = glossary[line]  # handle generic plural
except FileNotFoundError:
    warnings.warn('can not parse glossary.rst; see GitHub issue #1')


# the whole injection process is implemented quit clumsy, but it works for now
def injectGlossaryLinks(text: str):
    text = text + ' '  # add extra space to avoid index errors
    terms = list()
    letter = '_abcdefghijklmnopqrstuvwxyz'
    letter = letter + letter.upper()

    # mask out all weblinks to avoid term injection here (addresses issue #741)
    links = utilsFindWeblinks(text)
    for i, link in enumerate(links):
        replacer = f'${i}$'
        text = text.replace(link, replacer)

    for k in reversed(sorted(glossary.keys(), key=len)):  # long terms first to avoid term corruption
        url = glossary[k]
        ilast = 0
        while True:
            i0 = text.find(k, ilast)
            if i0 == -1:
                k = k[0].upper() + k[1:]
                i0 = text.find(k, ilast)
            if i0 == -1:
                break
            ilast = i0 + 1

            # continue if term isn't a seperate word
            if i0 > 0:
                if text[i0 - 1].lower() in letter:
                    continue
            if text[i0 + len(k)].lower() in letter:
                continue

            # if text[i0 + len(k)].lower() in letter:
            #    continue

            # handle some special cases
            if k.lower() == 'output':
                if text[i0:].lower().startswith('output data type'):
                    continue
                if text[i0:].lower().startswith('output format'):
                    continue
                if text[i0:].lower().startswith('output raster'):
                    continue
                if text[i0:].lower().startswith('output report'):
                    continue
                if text[i0:].lower().startswith('output destination'):
                    continue
                if text[i0:].lower().startswith('output category'):
                    continue
                if text[i0:].lower().startswith('output vector'):
                    continue
                if text[i0:].lower().startswith('output _'):
                    continue

            if k.lower() == 'target':
                if text[i0:].lower().startswith('target coordinate reference system'):
                    continue
                if text[i0:].lower().startswith('target extent'):
                    continue
                if text[i0:].lower().startswith('target raster'):
                    continue
                if text[i0:].lower().startswith('target width'):
                    continue
                if text[i0:].lower().startswith('target height'):
                    continue
                if text[i0:].lower().startswith('target grid'):
                    continue

            k2 = f'_{len(terms)}_'
            terms.append((k, k2, url))
            text = text[:i0] + k2 + text[i0 + len(k):]  # mark term

            break  # only link first appearence

    for k, k2, url in terms:
        link = f'<a href="{url}">{k}</a>'
        text = text.replace(k2, link)  # inject link

    # restore masled weblinks
    for i, link in enumerate(links):
        replacer = f'${i}$'
        text = text.replace(replacer, link)

    text = text[:-1]  # remove extra space
    return text


def utilsFindWeblinks(text) -> List[str]:
    match_: re.Match
    starts = [match_.start() for match_ in re.finditer('<a href="', text)]
    ends = [match_.start() + 4 for match_ in re.finditer('</a>', text)]
    assert len(starts) == len(ends)
    links = [text[start:end] for start, end in zip(starts, ends)]
    return links


def test():
    text = 'wavelength is a term that is also included in wavelength units. and again wavelength. \n' \
           'thisisnotawavelength wavelength \n' \
           'wavelengthNO wavelength. \n' \
           'Wavelength \n' \
           'No data valueE \n' \
           '"No data values"'

    # text = '"No data value"'
    print(injectGlossaryLinks(text))

# test()
