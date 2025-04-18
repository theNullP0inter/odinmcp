#!/bin/bash

set -eu

reload=false
rootPath="/"

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --reload)
            reload=true
            shift # past argument
            ;;
        --root-path)
            if [[ -n "${2-}" ]]; then
                rootPath="$2"
                shift 2 # past flag and its value
            else
                echo "Error: --root-path requires a value" >&2
                exit 1
            fi
            ;;
        *)    # unknown option
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
    esac
done

if $reload; then
    >&2 echo "Reload detected; running reload commands"
    >&2 printf "\n\nStarting local server: :80\n\n"
    cd /app
    uvicorn web.app:app --host "" --port 80 --reload --reload-dir /app --root-path "$rootPath"
else
    >&2 printf "\n\nStarting Production server: :80\n\n"
    cd /app
    uvicorn web.app:app --host "" --port 80 --root-path "$rootPath"
fi