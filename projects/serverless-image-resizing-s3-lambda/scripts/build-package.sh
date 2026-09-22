#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${project_root}/build"
package_file="${project_root}/lambda-image-resizer.zip"

rm -rf "${build_dir}"
rm -f "${package_file}"
mkdir -p "${build_dir}"

python3 -m pip install \
  --requirement "${project_root}/requirements.txt" \
  --target "${build_dir}" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all:

cp "${project_root}/src/lambda_function.py" "${build_dir}/"
(cd "${build_dir}" && zip -qr "${package_file}" .)

printf 'Created %s\n' "${package_file}"
