#!/bin/bash
set -ex

python -m pip install . -vv --no-deps --no-build-isolation

# Copy examples and notebooks to share directory
SHARE_DIR="${PREFIX}/share/pyvis"
mkdir -p "${SHARE_DIR}/examples" "${SHARE_DIR}/notebooks"
cp examples/*.py "${SHARE_DIR}/examples/"
cp notebooks/*.ipynb notebooks/*.csv notebooks/*.dot "${SHARE_DIR}/notebooks/" 2>/dev/null || true
