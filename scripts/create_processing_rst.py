import re
import subprocess
from os import makedirs
from os.path import abspath, join, dirname, exists, basename
from shutil import rmtree
from typing import List

from qgis.core import QgsProcessingParameterDefinition, QgsProcessingDestinationParameter

from enmapboxprocessing.algorithm.algorithms import algorithms
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.glossary import injectGlossaryLinks

import enmapbox

try:
    enmapboxdocumentation = __import__('enmapboxdocumentation')
except ModuleNotFoundError as ex:
    raise ex

dryRun = False  # a fast way to check if all parameters are documented


def generateRST():
    # create folder
    rootCodeRepo = abspath(join(dirname(enmapbox.__file__), '..'))
    rootDocRepo = abspath(join(dirname(enmapboxdocumentation.__file__), '..'))
    print(rootCodeRepo)
    print(rootDocRepo)

    rootRst = join(rootDocRepo, 'source', 'usr_section', 'usr_manual', 'processing_algorithms')
    print(rootRst)

    if exists(rootRst):
        print('Delete root folder')
        rmtree(rootRst)
    makedirs(rootRst)

    groups = dict()

    nalg = 0
    algs = algorithms()
    # from enmapboxprocessing.algorithm.rasterlayerzonalaggregationalgorithm import RasterLayerZonalAggregationAlgorithm
    # algs = [RasterLayerZonalAggregationAlgorithm()]
    for alg in algs:
        # print(alg.displayName())
        if Group.Experimental.name in alg.group():
            raise RuntimeError('Remove experimental algorithms from final release!')
        if alg.group() not in groups:
            groups[alg.group()] = dict()
        groups[alg.group()][alg.displayName()] = alg
        nalg += 1

    print(f'Found {nalg} algorithms.')

    textProcessingAlgorithmsRst = '''Processing Algorithms
*********************

.. toctree::
    :maxdepth: 1

'''

    for gkey in sorted(groups.keys()):

        # create group folder
        groupId = gkey.lower()
        for c in ' ,*':
            groupId = groupId.replace(c, '_')
        groupFolder = join(rootRst, groupId)
        makedirs(groupFolder)

        textProcessingAlgorithmsRst += '\n    {}/index.rst'.format(basename(groupFolder))

        # create group index.rst
        text = '''.. _{}:\n\n{}
{}

.. toctree::
   :maxdepth: 0
   :glob:

   *
'''.format(gkey, gkey, '=' * len(gkey))
        filename = join(groupFolder, 'index.rst')
        with open(filename, mode='w', encoding='utf-8') as f:
            f.write(text)

        for akey in groups[gkey]:

            algoId = akey.lower()
            for c in [' ']:
                algoId = algoId.replace(c, '_')

            text = '''.. _{}:

{}
{}
{}

'''.format(akey, '*' * len(akey), akey, '*' * len(akey))

            alg = groups[gkey][akey]
            print(alg)
            if isinstance(alg, EnMAPProcessingAlgorithm):
                alg.initAlgorithm()
                text = v3(alg, text)
            else:
                print(f'skip {alg}')
                continue
                # assert 0

            filename = join(groupFolder, '{}.rst'.format(algoId))
            for c in r'/()':
                filename = filename.replace(c, '_')
            with open(filename, mode='w', encoding='utf-8') as f:
                f.write(text)

    filename = join(rootRst, 'processing_algorithms.rst')
    with open(filename, mode='w', encoding='utf-8') as f:
        f.write(textProcessingAlgorithmsRst)
    print('created RST file: ', filename)


def v3(alg: EnMAPProcessingAlgorithm, text):
    try:
        helpParameters = {k: v for k, v in alg.helpParameters()}
    except Exception:
        assert 0

    text += injectGlossaryLinks(alg.shortDescription()) + '\n\n'

    text += '**Parameters**\n\n'
    outputsHeadingCreated = False
    for pd in alg.parameterDefinitions():
        assert isinstance(pd, QgsProcessingParameterDefinition)

        pdhelp = helpParameters.get(pd.description(), 'undocumented')
        if pdhelp == '':  # an empty strings has to be set by the algo to actively hide an parameter
            continue
        if pdhelp == 'undocumented':  # 'undocumented' is the default and must be overwritten by the algo!
            assert 0, pd.description()

        if not outputsHeadingCreated and isinstance(pd, QgsProcessingDestinationParameter):
            text += '**Outputs**\n\n'
            outputsHeadingCreated = True

        text += '\n:guilabel:`{}` [{}]\n'.format(pd.description(), pd.type())

        pdhelp = injectGlossaryLinks(pdhelp)

        if False:  # todo pd.flags() auswerten
            text += '    Optional\n'

        for line in pdhelp.split('\n'):
            text += '    {}\n'.format(line)

        text += '\n'

        if pd.defaultValue() is not None:
            if isinstance(pd.defaultValue(), str) and '\n' in pd.defaultValue():
                text += '    Default::\n\n'
                for line in pd.defaultValue().split('\n'):
                    text += '        {}\n'.format(line)
            else:
                text += '    Default: *{}*\n\n'.format(pd.defaultValue())

    if dryRun:
        return ''

    # convert HTML weblinks into RST weblinks
    htmlLinks = utilsFindHtmlWeblinks(text)
    for htmlLink in htmlLinks:
        rstLink = utilsHtmlWeblinkToRstWeblink(htmlLink)
        text = text.replace(htmlLink, rstLink)

    # add qgis_process help
    algoId = 'enmapbox:' + alg.name()
    print(algoId)
    result = subprocess.run(['qgis_process', 'help', algoId], stdout=subprocess.PIPE)
    helptext = result.stdout.decode('cp1252')  # use Windows codepage 1252 to avoid problems with special characters
    helptext = helptext[helptext.find('----------------\nArguments\n----------------'):]
    helptext = '\n'.join(['    ' + line for line in helptext.splitlines()])

    text += '**Command-line usage**\n\n' \
            f'``>qgis_process help {algoId}``::\n\n'
    text += helptext

    return text


def utilsFindHtmlWeblinks(text) -> List[str]:
    match_: re.Match
    starts = [match_.start() for match_ in re.finditer('<a href="', text)]
    ends = [match_.start() + 4 for match_ in re.finditer('</a>', text)]
    assert len(starts) == len(ends)
    links = [text[start:end] for start, end in zip(starts, ends)]
    return links


def utilsHtmlWeblinkToRstWeblink(htmlText: str) -> str:
    assert htmlText.startswith('<a href="'), htmlText
    assert htmlText.endswith('</a>'), htmlText
    link, name = htmlText[9:-4].split('">')
    rstText = f'`{name} <{link}>`_'
    return rstText


if __name__ == '__main__':
    generateRST()
