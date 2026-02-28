${PYTHON} -m pip install . -vv --no-deps --no-build-isolation

# Install examples and notebooks to share directory
SHARE_DIR="${PREFIX}/share/pyvis"
mkdir -p "${SHARE_DIR}/examples"
mkdir -p "${SHARE_DIR}/notebooks"
cp -r examples/*.py "${SHARE_DIR}/examples/"
cp -r notebooks/*.ipynb notebooks/*.csv notebooks/*.dot "${SHARE_DIR}/notebooks/" 2>/dev/null || true
