import os
from _classic.enmapboxgeoalgorithms.provider import Help

def parseFolder(package):
    estimators = dict()
    exec('import ' + package)
    dir = eval('os.path.dirname({package}.__file__)'.format(package=package))
    for basename in os.listdir(dir):
        if basename.startswith('_'): continue
        if basename.endswith('.pyc'): continue
        if os.path.splitext(basename)[0].endswith('Help'): continue
        if os.path.splitext(basename)[0].endswith('PostCode'): continue

        name = basename.replace('.py', '')

        # get code snipped
        with open(os.path.join(dir, name + '.py')) as f:
            code = f.readlines()
            code = ''.join(code)

        # get post code snipped
        filename = os.path.join(dir, name + 'PostCode.py')
        if os.path.exists(filename):
            with open(filename) as f:
                postCode = f.readlines()
                postCode = ''.join(postCode)
        else:
            postCode = None

        # get help
        helpFile = os.path.join(dir, name+'Help.py')
        namespace = dict()
        if os.path.exists(helpFile):
            with open(helpFile) as f:
                codeHelp = f.readlines()
                codeHelp = ''.join(codeHelp)
            exec(codeHelp, None, namespace)

        helpAlg = namespace.get('helpAlg', Help('undocumented'))
        helpCode = namespace.get('helpCode', Help('undocumented'))

        estimators[name] = code, helpAlg, helpCode, postCode
    return estimators

def parseRegressors():
    return parseFolder(package='_classic.enmapboxgeoalgorithms.estimators.regressors')

def parseClassifiers():
    return parseFolder(package='_classic.enmapboxgeoalgorithms.estimators.classifiers')

def parseClusterers():
    return parseFolder(package='_classic.enmapboxgeoalgorithms.estimators.clusterers')

def parseTransformers():
    return parseFolder(package='_classic.enmapboxgeoalgorithms.estimators.transformers')
