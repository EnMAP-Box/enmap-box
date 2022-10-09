#!/usr/bin/env bash


if [ -z "$QGIS_TEST_VERSION" ]; then
  export QGIS_TEST_VERSION=latest # See https://hub.docker.com/r/qgis/qgis/tags/
fi

cd $(dirname $0)/..
export GITHUB_WORKSPACE=$PWD # only for local execution
ls -l /usr/src
docker-compose -f .docker/docker-compose.gh.yml run qgis /usr/src/.docker/run-docker-tests.sh $@
docker-compose -f .docker/docker-compose.gh.yml rm -s -f
# requires that https://github.com/nektos/act is installed
# cd ..
# ~/bin/act -j test