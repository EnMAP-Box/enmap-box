from os import remove
from os.path import basename, dirname, join, abspath

def createDocPrint(pyfile):
    root = dirname(pyfile)
    log = join(root, basename(pyfile).replace('.py', '.txt'))
    try:
        remove(log)
    except:
        pass

    def print(obj):
        with open(log, 'a') as file:
            file.write('{}\n'.format(obj))

    return print

def createReportSaveHTML():
    from _classic.hubflow.report import Report
    oldSaveHTML = Report.saveHTML

    def saveHTML(self, filename, open=False):
        filename = abspath(join('../../_static', filename))
        oldSaveHTML(self, filename=filename, open=False)

    return saveHTML

def createPyPlotSavefig(filename):
    from _classic.hubflow.core import plt
    oldSavefig = plt.savefig

    def savefig(*args):
        oldSavefig(filename)

    return savefig

def createClassLegend(pyfile, names, colors, i=''):
    root = dirname(pyfile)
    html = join(root, basename(pyfile).replace('.py', '{}.html'.format(i)))

    text = '''
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    table, th, td {
      border: 1px solid black;
    }
    </style>
    </head>
    <body>
    
    <table>
      <tr>
        <td style="color:#FFFFFF">.....</td>
        <th>Classes</th>
      </tr>
      <tr>
    '''

    for name, color in zip(names, colors):
        assert isinstance(color, str)
        assert isinstance(name, str)

        text += '''
        <tr>
        <td style="background-color:{}"></td>
        <th>{}</th>
        </tr>'''.format(color, name)

    text += '''
    </table>
    
    </body>
    </html>
    '''

    with open(html, 'w') as file:
        file.write(text)

