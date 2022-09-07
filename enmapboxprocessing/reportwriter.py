from typing import TextIO, List, Tuple, Union

from typeguard import typechecked


@typechecked
class HtmlReportWriter(object):

    def __init__(self, file: TextIO):
        self.file = file

    def writeHeader(self, value):
        self.file.writelines(['<h1>', value, '</h1>', '\n'])

    def writeSubHeader(self, value):
        self.file.writelines(['<h2>', value, '</h2>', '\n'])

    def writeParagraph(self, value):
        self.file.writelines(['<p>', value, '</p>', '\n'])

    def writeImage(self, value):
        self.file.writelines(['<p><img src="', value, '"/></p>', '\n'])

    def writeTable(
            self, values: List[List], caption: str = None, columnHeaders: List[str] = None,
            rowHeaders: List[str] = None, columnMainHeaders: List[Tuple[str, int]] = None
    ):
        self._writeTableStart(caption)

        if rowHeaders is None:
            upperLeftCellHeader = None
        else:
            upperLeftCellHeader = ''

        if columnMainHeaders is not None:
            self._writeTableColumnMainHeader([t[0] for t in columnMainHeaders], [t[1] for t in columnMainHeaders])

        if columnHeaders is not None:
            self._writeTableColumnHeader(columnHeaders, upperLeftCellHeader=upperLeftCellHeader)
        if rowHeaders is None:
            for rowValues in values:
                self._writeTableRow(rowValues)
        else:
            for rowValues, rowHeader in zip(values, rowHeaders):
                self._writeTableRow(rowValues, header=rowHeader)

        self._writeTableEnd()

    def _writeTableStart(self, caption: str = None):
        self.file.writelines(['<p><table border="1" cellspacing="0" cellpadding="10" style="white-space:nowrap;">'])
        if caption is not None:
            self.file.writelines([f'<caption style="text-align:left">{caption}</caption>'])

    def _writeTableEnd(self):
        self.file.writelines(['</table></p>'])

    def _writeTableColumnHeader(self, values, upperLeftCellHeader: str = None):
        self.file.writelines(['<tr>'])
        if upperLeftCellHeader is not None:
            self.file.writelines([f'<td>{upperLeftCellHeader}</td>'])
        self.file.writelines([f'<th scope="col">{value}</th>' for value in values])
        self.file.writelines(['</tr>'])

    def _writeTableColumnMainHeader(self, values: List, spans: List[int]):
        assert len(values) == len(spans)
        self.file.writelines(['<col>'])
        for span in spans:
            self.file.writelines([f'<colgroup span="{span}"></colgroup>'])
        self.file.writelines(['<tr><td rowspan="1"></td>'])
        for span, value in zip(spans, values):
            self.file.writelines([f'<th colspan="{span}" scope="colgroup">{value}</th>'])
        self.file.writelines(['</tr>'])

    def _writeTableRow(self, values: List, header=None):
        self.file.writelines(['<tr>'])
        if header is not None:
            self.file.writelines([f'<th scope="row">{header}</th>'])
        self.file.writelines([f'<td>{str(value)}</td>' for value in values])
        self.file.writelines(['</tr>'])


@typechecked
class CsvReportWriter(object):

    def __init__(self, file: TextIO):
        self.file = file

    def writeHeader(self, value):
        self.file.writelines([value, '\n'])

    def writeSubHeader(self, value):
        self.file.writelines([value, '\n'])

    def writeParagraph(self, value):
        self.file.writelines([value, '\n'])

    def writeImage(self, *args, **kwargs):
        pass

    def writeTable(
            self, values: List[List], caption: str = None, columnHeaders: List[str] = None,
            rowHeaders: List[str] = None, columnMainHeaders: List[Tuple[str, int]] = None
    ):
        self._writeTableStart(caption)

        if rowHeaders is None:
            upperLeftCellHeader = None
        else:
            upperLeftCellHeader = ' '

        if columnMainHeaders is not None:
            self._writeTableColumnMainHeader(
                [t[0] for t in columnMainHeaders], [t[1] for t in columnMainHeaders], upperLeftCellHeader)

        if columnHeaders is not None:
            self._writeTableColumnHeader(columnHeaders, upperLeftCellHeader=upperLeftCellHeader)
        if rowHeaders is None:
            for rowValues in values:
                self._writeTableRow(rowValues)
        else:
            for rowValues, rowHeader in zip(values, rowHeaders):
                self._writeTableRow(rowValues, header=rowHeader)

    def _writeTableStart(self, caption: str = None):
        if caption is not None:
            self.file.writelines([caption, '\n'])

    def _writeTableColumnHeader(self, values, upperLeftCellHeader: str = None):
        if upperLeftCellHeader is not None:
            values = [upperLeftCellHeader] + values
        self.file.writelines([';'.join(values), '\n'])

    def _writeTableColumnMainHeader(self, values: List, spans: List[int], upperLeftCellHeader: str = None):
        assert len(values) == len(spans)
        _values = list()
        if upperLeftCellHeader is not None:
            _values.append(upperLeftCellHeader)
        for value, span in zip(values, spans):
            _values.append(value)
            for i in range(span - 1):
                _values.append(' ')
        self.file.writelines([';'.join(_values), '\n'])

    def _writeTableRow(self, values: List, header=None):
        if header is not None:
            values = [header] + values
        self.file.writelines([';'.join(map(str, values)), '\n'])


@typechecked
class MultiReportWriter(object):

    def __init__(self, reports: List[Union[HtmlReportWriter, CsvReportWriter]]):
        self.reports = reports

    def writeHeader(self, value):
        for report in self.reports:
            report.writeHeader(value)

    def writeSubHeader(self, value):
        for report in self.reports:
            report.writeSubHeader(value)

    def writeParagraph(self, *value):
        value = ' '.join(map(str, value))
        for report in self.reports:
            report.writeParagraph(value)

    def writeImage(self, value):
        for report in self.reports:
            report.writeImage(value)

    def writeTable(
            self, values: List[List], caption: str = None, columnHeaders: List[str] = None,
            rowHeaders: List[str] = None, columnMainHeaders: List[Tuple[str, int]] = None
    ):
        for report in self.reports:
            report.writeTable(values, caption, columnHeaders, rowHeaders, columnMainHeaders)
