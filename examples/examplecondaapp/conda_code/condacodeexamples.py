import sys


def return_sysinfo():
    info = ['System Info']

    info.append('Executable: {}'.format(sys.executable))
    info.append('PYTHONPATH')

    for p in sorted(sys.path):
        info.append(p)

    return '\n'.join(info)


if __name__ == '__main__':
    print(return_sysinfo())
