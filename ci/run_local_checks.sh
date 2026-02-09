#!/usr/bin/env bash
set -euo pipefail

pushd backend >/dev/null
pip install -r requirements.txt
black app tests
isort app tests
pytest -q
popd >/dev/null

pushd frontend >/dev/null
npm install
npm run lint
npm run build
popd >/dev/null
