from urlchecker.core.check import UrlChecker
from pathlib import Path

path_enmap = Path(__file__).parents[1] / 'enmapbox'

file_types = ['.rst', '.md', '.py']
exclude_files = ['/pyqtgraph/', 'pyqtgraph']
exclude_patterns = ['type=xyz', '%7Bx%7D', '&zmin=']
exclude_urls = []

checker = UrlChecker(path=path_enmap.as_posix(),
                     file_types=file_types,
                     exclude_files=exclude_files, print_all=True,
                     serial=True)


r = checker.run(
    exclude_urls=exclude_urls,
    exclude_patterns=exclude_patterns,
    retry_count=3,
    timeout=5
)
s = ""
