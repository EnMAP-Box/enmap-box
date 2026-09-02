#!/usr/bin/env bash
# Run the python3 of the qgis/qgis docker image as if it was a local interpreter.
#
# Usage in PyCharm:
#   Settings > Project > Python Interpreter > Add Interpreter > Add Local Interpreter
#   > Select existing > Type: Python > Python path: <repo>/scripts/docker-python.sh
#
# The container mounts the repository and $HOME at their host paths, so every path
# PyCharm sends (source files, its own helper scripts, temp files) resolves inside
# the container exactly as it does outside.
#
# Environment overrides:
#   ENMAPBOX_DOCKER_IMAGE   docker image to use            (default: qgis/qgis:latest)
#   ENMAPBOX_DOCKER_MOUNTS  extra "-v" arguments, space separated
#   ENMAPBOX_DOCKER_OPTS    extra "docker run" arguments, space separated
#   ENMAPBOX_DOCKER_DISPLAY 1 = forward the X11 display instead of running offscreen
#
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

IMAGE="${ENMAPBOX_DOCKER_IMAGE:-qgis/qgis:latest}"

# PYTHONPATH as in scripts/setup_env.bat, plus the QGIS python packages of the image.
CONTAINER_PYTHONPATH="/usr/share/qgis/python:/usr/share/qgis/python/plugins"
CONTAINER_PYTHONPATH="${CONTAINER_PYTHONPATH}:${REPO}"
CONTAINER_PYTHONPATH="${CONTAINER_PYTHONPATH}:${REPO}/site-packages"
CONTAINER_PYTHONPATH="${CONTAINER_PYTHONPATH}:${REPO}/tests/src"
if [[ -n "${PYTHONPATH:-}" ]]; then
    CONTAINER_PYTHONPATH="${CONTAINER_PYTHONPATH}:${PYTHONPATH}"
fi

ARGS=(
    run --rm
    --network host                       # let the PyCharm debugger talk back to the IDE
    --user "$(id -u):$(id -g)"           # keep files created in the repo owned by us
    --workdir "$(pwd)"
    -e "HOME=${HOME}"
    -e "PYTHONPATH=${CONTAINER_PYTHONPATH}"
    -e PYTHONUNBUFFERED=1
    -e PYTHONDONTWRITEBYTECODE=1
    -e QGIS_DISABLE_MESSAGE_HOOKS=1
    -e QGIS_NO_OVERRIDE_IMPORT=1
    -e CI=True
    -v "${REPO}:${REPO}"
    -v "${HOME}:${HOME}"
    -v /tmp:/tmp
)

# PyCharm may run the interpreter from a directory outside the repo (e.g. its helpers).
CWD="$(pwd)"
case "${CWD}" in
    "${REPO}"/*|"${REPO}"|"${HOME}"/*|"${HOME}"|/tmp/*|/tmp) ;;
    *) ARGS+=(-v "${CWD}:${CWD}") ;;
esac

if [[ "${ENMAPBOX_DOCKER_DISPLAY:-0}" == "1" && -n "${DISPLAY:-}" ]]; then
    ARGS+=(
        -e "DISPLAY=${DISPLAY}"
        -e "XAUTHORITY=${XAUTHORITY:-${HOME}/.Xauthority}"
        -v /tmp/.X11-unix:/tmp/.X11-unix
    )
else
    ARGS+=(-e QT_QPA_PLATFORM=offscreen)
fi

# Interactive only when there really is a terminal, otherwise PyCharm's pipes break.
if [[ -t 0 ]]; then
    ARGS+=(-it)
else
    ARGS+=(-i)
fi

if [[ -n "${ENMAPBOX_DOCKER_MOUNTS:-}" ]]; then
    read -r -a extra_mounts <<< "${ENMAPBOX_DOCKER_MOUNTS}"
    ARGS+=("${extra_mounts[@]}")
fi
if [[ -n "${ENMAPBOX_DOCKER_OPTS:-}" ]]; then
    read -r -a extra_opts <<< "${ENMAPBOX_DOCKER_OPTS}"
    ARGS+=("${extra_opts[@]}")
fi

if ! docker image inspect "${IMAGE}" > /dev/null 2>&1; then
    # Pull chatter must not end up on stdout, PyCharm parses it.
    docker pull "${IMAGE}" 1>&2
fi

exec docker "${ARGS[@]}" "${IMAGE}" python3 "$@"
