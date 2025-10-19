#!/bin/bash

NAME="datadigitizer"
PYNAME="py$NAME"
PY_SRC="./src/$PYNAME"

# environment variables
PLATFORM="linux"

if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    DEFAULT_INSTALL_DIR="${APPDATA//\\//}/local"
    PLATFORM="windows"
fi

if [[ "$OSTYPE" == "darwin"* ]];then
    PLATFORM="darwin"
fi

export NAME
echo "NAME=" $NAME

export PLATFORM
echo "PLATFORM=" $PLATFORM

export PY_SRC
echo "PY_SRC=" $PY_SRC


