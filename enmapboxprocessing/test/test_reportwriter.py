from enmapboxprocessing.reportwriter import HtmlReportWriter, CsvReportWriter, MultiReportWriter
from enmapboxprocessing.test.testcase import TestCase


class TestReportWriter(TestCase):

    def test(self):
        filenameHtml = self.filename('reportWriter.html')
        filenameCsv = self.filename('reportWriter.csv')
        with open(filenameHtml, 'w') as fileHtml, open(filenameCsv, 'w') as fileCsv:
            report = MultiReportWriter([HtmlReportWriter(fileHtml), CsvReportWriter(fileCsv)])
            report.writeHeader('Header 1')
            report.writeSubHeader('Header 2')
            report.writeParagraph(
                'Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.')
            values = [[11, 12], [21, 22], [31, 32]]
            report.writeTable(values, caption='Table without Header')
            report.writeTable(values, columnHeaders=['Column 1', 'Column 2'], caption='Table with Column Header')
            report.writeTable(values, rowHeaders=['Row 1', 'Row 2', 'Row 3'], caption='Table with Row Header')
            report.writeTable(
                values, columnHeaders=['Column 1', 'Column 2'], rowHeaders=['Row 1', 'Row 2', 'Row 3'],
                caption='Table with Row and Column Header'
            )
            report.writeTable(
                values, columnHeaders=['Column 1', 'Column 2'], rowHeaders=['Row 1', 'Row 2', 'Row 3'],
                columnMainHeaders=[('Big Column', 2)],
                caption='Table with Double Column Header'
            )

    def test2(self):
        import csv
        with open(self.filename('eggs.csv'), 'w', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=';', dialect=csv.excel(),
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow(['Spam'] * 5 + ['Baked Beans'])
            spamwriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])
            spamwriter.writerow([1.46])

    def test3(self):
        import csv

        with open(self.filename('eggs.csv'), 'w', encoding='utf-8') as f:
            writer = csv.writer(f, dialect=csv.excel(), delimiter=';')
            writer.writerow(['A', 'B', 'C'])
            writer.writerow([1, 42.32, 1.46])
