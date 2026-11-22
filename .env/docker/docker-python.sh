#!/usr/bin/env bash
# Run the python3 of the test image as if it was a local interpreter.
#
# The image is the one described by .docker/docker-compose.gh.yml, i.e. it is built
# from .docker/Dockerfile and therefore contains the extra requirements
# (requirements.txt plus the apt packages) that the CI tests use.
#
# Usage in PyCharm:
#   Settings > Project > Python Interpreter > Add Interpreter > Add Local Interpreter
#   > Select existing > Type: Python > Python path: <repo>/.docker/docker-python.sh
#
# The container mounts the repository at their host paths, so every path
# PyCharm sends (source files, its own helper scripts, temp files) resolves inside
# the container exactly as it does outside.
#
# Environment overrides:
#   QGIS_VERSION       tag of the qgis/qgis base image      (default: latest)
#   DOCKER_IMAGE       use this image instead of building it from the compose file
#   DOCKER_BUILD       1 = (re)build the image before running
#   DOCKER_MOUNTS      extra "-v" arguments, space separated
#   DOCKER_OPTS        extra "docker run" arguments, space separated
#   DOCKER_DISPLAY     1 = forward the X11 display instead of running offscreen
#
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.gh.yml"
COMPOSE_SERVICE=qgis
QGIS_VERSION="${QGIS_VERSION:-latest}"

# Compose project names must not contain dots, e.g. "3.40" -> "3-40".
COMPOSE_PROJECT="enmapbox-${QGIS_VERSION//[^a-zA-Z0-9_-]/-}"
COMPOSE_PROJECT="$(printf '%s' "${COMPOSE_PROJECT}" | tr '[:upper:]' '[:lower:]')"

# docker-compose.gh.yml expects both variables; GITHUB_WORKSPACE is only used for the
# /usr/src mount of the CI run, which we replace by our own mounts below.
export QGIS_VERSION
export GITHUB_WORKSPACE="${GITHUB_WORKSPACE:-${REPO}}"

xhost +local:docker >/dev/null 2>&1 || true

if [[ -n "${DISPLAY:-}" ]]; then
    DOCKER_DISPLAY=1
else
    DOCKER_DISPLAY=0
fi

compose() {
    docker compose -f "${COMPOSE_FILE}" -p "${COMPOSE_PROJECT}" "$@"
}

if [[ -n "${DOCKER_IMAGE:-}" ]]; then
    IMAGE="${DOCKER_IMAGE}"
else
    # Ask compose for the image name it tags the built service with.
    IMAGE="$(compose config --images "${COMPOSE_SERVICE}" 2>/dev/null | head -n1)"
    IMAGE="${IMAGE:-${COMPOSE_PROJECT}-qgis}"
fi

# The Dockerfile sets PYTHONPATH to the QGIS paths.
# We only add the repo paths that are mounted to the container.
# CONTAINER_PYTHONPATH="${PYTHONPATH:-/usr/share/qgis/python:/usr/share/qgis/python/plugins:/usr/lib/python3/dist-packages/qgis:/usr/share/qgis/python/qgis}"
CONTAINER_PYTHONPATH="/usr/share/qgis/python:/usr/share/qgis/python/plugins:${REPO}:${REPO}/tests:"

ARGS=(
    run --rm
    --network host                       # let the PyCharm debugger talk back to the IDE
    --user "$(id -u):$(id -g)"           # keep files created in the repo owned by us
    --workdir "${REPO}"
    -e "PYTHONPATH=${CONTAINER_PYTHONPATH}"
    -e PYTHONUNBUFFERED=1
    -e PYTHONDONTWRITEBYTECODE=1
    -e QGIS_DISABLE_MESSAGE_HOOKS=1
    -e QGIS_NO_OVERRIDE_IMPORT=1
    -v "${REPO}:${REPO}"
    -e QGIS_LOCAL_STORAGE_PATH="${HOME}/.local/share/QGIS/QGIS3"
    -v "${HOME}:${HOME}"
    -v /tmp:/tmp
)

# PyCharm may run the interpreter from a directory outside the repo (e.g. its helpers).
CWD="$(pwd)"
case "${CWD}" in
    "${REPO}"/*|"${REPO}"|/tmp/*|/tmp) ;;
    *) ARGS+=(-v "${CWD}:${CWD}") ;;
esac

if [[ "${DOCKER_DISPLAY:-0}" == "1" && -n "${DISPLAY:-}" ]]; then
    ARGS+=(
        -e "DISPLAY=${DISPLAY}"
        -e "XAUTHORITY=${XAUTHORITY:-/root/.Xauthority}"
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

# Detect if PyCharm is running with debugger (debugpy or pydevd)
# PyCharm passes --host and --port arguments to the interpreter when debugging
if [[ "${@}" == *"--host"* ]] || [[ "${@}" == *"--port"* ]] || [[ "${@}" == *"-m debugpy"* ]]; then
    # Debug mode detected - ensure container can reach host
    # The --network host flag above should handle this, but we also need to ensure
    # debugpy binds to 0.0.0.0 instead of 127.0.0.1 to be accessible from the host
    echo "PyCharm debugger detected" >&2
    # PyCharm's debugpy will handle the host:port mapping, but we ensure
    # the container can reach the host via --network host
fi

if [[ -n "${DOCKER_MOUNTS:-}" ]]; then
    read -r -a extra_mounts <<< "${DOCKER_MOUNTS}"
    ARGS+=("${extra_mounts[@]}")
fi
if [[ -n "${DOCKER_OPTS:-}" ]]; then
    read -r -a extra_opts <<< "${DOCKER_OPTS}"
    ARGS+=("${extra_opts[@]}")
fi

# Check if debugpy/pydevd is being used by checking arguments
# PyCharm passes -m debugpy --host 127.0.0.1 --port XXXX when debugging
DEBUGPY_ARGS=()
for arg in "$@"; do
    if [[ "$arg" == "--host" ]] || [[ "$arg" == "--port" ]] || [[ "$arg" == *"-m debugpy"* ]] || [[ "$arg" == *"-m pydevd"* ]]; then
        DEBUGPY_ARGS+=("$arg")
    fi
done

if [[ ${#DEBUGPY_ARGS[@]} -gt 0 ]]; then
    echo "PyCharm debugger detected. Arguments: ${DEBUGPY_ARGS[*]}" >&2
    # PyCharm uses pydevd which works with --network host
    # No additional environment variables needed
fi

if [[ "${DOCKER_BUILD:-0}" == "1" ]] || ! docker image inspect "${IMAGE}" > /dev/null 2>&1; then
    # Build chatter must not end up on stdout, PyCharm parses it.
    if [[ -n "${DOCKER_IMAGE:-}" ]]; then
        docker pull "${IMAGE}" 1>&2
    else
        compose build "${COMPOSE_SERVICE}" 1>&2
    fi
fi

exec docker "${ARGS[@]}" "${IMAGE}" "python3" "$@"
