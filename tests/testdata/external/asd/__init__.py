from os.path import dirname, join
from os import listdir

folder_binary = join(dirname(__file__), 'asd')
folder_ascii = join(dirname(__file__), 'txt')

filenames_ascii = [join(folder_ascii, filename) for filename in listdir(folder_ascii) if filename.endswith('.txt')]
filenames_binary = [join(folder_binary, filename) for filename in listdir(folder_binary) if filename.endswith('.asd')]
