from typing import TextIO, List, Tuple, Union

from enmapbox.typeguard import typechecked


@typechecked
class HtmlReportWriter(object):

    def __init__(self, file: TextIO):
        self.file = file
        # Write the full HTML5 header, all CSS, and opening body/main tags.
        # This is offline-first and W3C compliant.
        self.file.write(r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EnMAP-Box Report</title>
    <style>
      /* 1. Base setup (from The Cascade) */
      :root {
        /* EnMAP-Box inspired colors (offline-friendly) */
        --color-primary: #004b5a; /* A dark teal */
        --color-text: #333;
        --color-bg: #ffffff;
        --color-bg-secondary: #f4f4f4;
        --color-border: #ddd;
      }

      @media (prefers-color-scheme: dark) {
        :root {
          --color-primary: #58a6ff; /* A light, accessible blue for dark mode */
          --color-text: #e0e0e0;
          --color-bg: #1e1e1e;
          --color-bg-secondary: #121212;
          --color-border: #444;
        }
      }

      /* 2. General Body Styling (Readability) */
      body {
        /* Offline-first system font stack */
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        line-height: 1.6;
        font-size: 1.1rem;
        color: var(--color-text);
        background-color: var(--color-bg-secondary);
        margin: 0;
        padding: 0;
      }

      /* 3. Main Content Wrapper (The Cascade layout) */
      main {
        max-width: min(90ch, 100% - 4rem); /* Readable width */
        margin: 2rem auto; /* Center the content */
        padding: 2rem;
        background-color: var(--color-bg);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      }

      @media (prefers-color-scheme: dark) {
        main {
          box-shadow: none;
          border: 1px solid var(--color-border);
        }
      }

      /* 4. Typography (Inspired by RTD) */
      h1, h2, h3, h4, h5, h6 {
        color: var(--color-primary);
        line-height: 1.3;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
      }

      h1 { font-size: 2.2rem; }
      h2 { font-size: 1.8rem; }
      h3 { font-size: 1.4rem; }

      p {
        margin-bottom: 1.2em;
      }

      a {
        color: var(--color-primary);
        text-decoration: none;
      }
      a:hover {
        text-decoration: underline;
      }

      /* 5. Responsive Media (from The Cascade) */
      img, svg, video {
        max-width: 100%;
        height: auto;
        display: block;
        border-radius: 4px;
      }

      /* 6. Table Styling (Common in reports) */
      table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1.5rem;
        font-size: 0.95rem;
      }

      th, td {
        border: 1px solid var(--color-border);
        padding: 0.75rem;
        text-align: left;
      }

      th {
        background-color: var(--color-bg-secondary);
        font-weight: 600;
      }

      caption {
        caption-side: bottom; /* Modern caption placement */
        text-align: left;
        font-style: italic;
        color: var(--color-text);
        padding: 0.5rem 0;
        margin-top: 0.5rem;
      }

    </style>
</head>
<body>
<main>
""")

    def close(self):
        """Writes the closing HTML tags."""
        try:
            # --- THIS IS THE ONLY CORRECT LINE ---
            # It MUST NOT contain </style>
            if self.file and not self.file.closed:
                self.file.write("\n</main>\n</body>\n</html>\n")
        except AttributeError:
            pass

    def __del__(self):
        """
        Destructor: Attempt to close when object is destroyed.
        This is a fallback, but explicit .close() is preferred.
        """
        self.close()

    def writeHeader(self, value):
        self.file.writelines(['<h1>', value, '</h1>', '\n'])

    def writeSubHeader(self, value):
        self.file.writelines(['<h2>', value, '</h2>', '\n'])

    def writeParagraph(self, value):
        self.file.writelines(['<p>', value, '</p>', '\n'])

    def writeImage(self, value):
        # Added alt="" for W3C validation
        self.file.writelines([f'<p><img src="{value}" alt="" /></p>', '\n'])

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
            # --- CORRECTED VARIABLE ---
            self._writeTableColumnHeader(columnHeaders, upperLeftCellHeader=upperLeftCellHeader)

        if rowHeaders is None:
            for rowValues in values:
                self._writeTableRow(rowValues)
        else:
            for rowValues, rowHeader in zip(values, rowHeaders):
                self._writeTableRow(rowValues, header=rowHeader)

        self._writeTableEnd()

    def _writeTableStart(self, caption: str = None):
        self.file.writelines(['<table style="white-space:nowrap;">'])
        if caption is not None:
            self.file.writelines([f'<caption>{caption}</caption>'])

    def _writeTableEnd(self):
        self.file.writelines(['</table>'])

    def _writeTableColumnHeader(self, values, upperLeftCellHeader: str = None):
        # --- CORRECTED VARIABLE ---
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

    def close(self):
        """No action needed for CSV writer, but good for interface."""
        pass

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
                self.file.writelines(self._formatRow(rowValues))
        else:
            for rowValues, rowHeader in zip(values, rowHeaders):
                self.file.writelines(self._formatRow(rowValues, header=rowHeader))

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

    def _formatRow(self, values: List, header=None):
        if header is not None:
            values = [header] + values
        return ';'.join(map(str, values)) + '\n'

    def _writeTableRow(self, values: List, header=None):
        self.file.writelines([self._formatRow(values, header)])


@typechecked
class MultiReportWriter(object):

    def __init__(self, reports: List[Union[HtmlReportWriter, CsvReportWriter]]):
        self.reports = reports

    def close(self):
        """Close all report writers in the list."""
        for report in self.reports:
            report.close()

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