#!/usr/bin/env bash
set -euo pipefail

outdir="${outdir:-./outdir}"
samplesheet="${input:-}"

if [ -z "$samplesheet" ] || [ ! -f "$samplesheet" ]; then
  echo "qc: missing input samplesheet: $samplesheet" >&2
  exit 1
fi

python="${PYTHON:-python3}"
if ! command -v "$python" >/dev/null 2>&1; then
  echo "qc: python3 is required to run FASTQ QC" >&2
  exit 1
fi

exec "$python" "$(dirname "$(readlink -f "$0")")/qc.py" "$samplesheet" "$outdir"
