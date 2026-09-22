#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
layer_dir="${project_root}/layer"
layer_file="${project_root}/pillow-layer-python312-x86_64.zip"

rm -rf "${layer_dir}"
rm -f "${layer_file}"
mkdir -p "${layer_dir}/python"

python3 -m pip install \
  --requirement "${project_root}/requirements.txt" \
  --target "${layer_dir}/python" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all:

(cd "${layer_dir}" && zip -qr "${layer_file}" python)

printf 'Created %s\n' "${layer_file}"
