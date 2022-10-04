#!/usr/bin/env bash
#***************************************************************************
#***************************************************************************
#
#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License as published by  *
#*   the Free Software Foundation; either version 2 of the License, or     *
#*   (at your option) any later version.                                   *
#*                                                                         *
#***************************************************************************

set -e

pushd /usr/src
DEFAULT_PARAMS='-x -v'
cd /usr/src

ls -l
export QT_QPA_PLATFORM=offscreen
export CI=True
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# python3 -m coverage run -m unittest discover -s tests
# xvfb-run pytest ${@:-`echo $DEFAULT_PARAMS`}
# python3 scripts/create_runtests.py
# xvfb-run scripts/runtests.sh
python3 scripts/setup_repository.py
python3 scripts/create_runtests.py
chmod +x scripts/runtests.sh
xvfb-run scripts/runtests.sh
popd