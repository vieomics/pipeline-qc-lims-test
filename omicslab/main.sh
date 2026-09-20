#!/usr/bin/env bash
set -euo pipefail

outdir="${outdir:-./outdir}"
samplesheet="${input:-}"
fail_samples="${QC_FAIL_SAMPLES:-}"

# The SDK localizes s3:// params (input, outdir) in params.json; the env
# values still hold the raw s3:// URIs, so prefer the localized paths.
if [ -f params.json ]; then
  localized="$(python3 -c "import json;d=json.load(open('params.json'));p=d.get('params') or d;print(p.get('input',''))" 2>/dev/null || true)"
  [ -n "$localized" ] && samplesheet="$localized"
  localized="$(python3 -c "import json;d=json.load(open('params.json'));p=d.get('params') or d;print(p.get('outdir',''))" 2>/dev/null || true)"
  [ -n "$localized" ] && outdir="$localized"
fi

if [ -z "$samplesheet" ] || [ ! -f "$samplesheet" ]; then
  echo "QC fixture: missing input samplesheet: $samplesheet" >&2
  exit 1
fi

mkdir -p "$outdir/qc" "$outdir/fastqc"
printf 'sample_id,status,total_reads,duplication,q30\n' > "$outdir/qc/qc_summary.csv"

while IFS=, read -r sample _rest; do
  [ -z "${sample:-}" ] && continue
  [ "$sample" = "sample" ] && continue
  sample="${sample%$'\r'}"
  status="pass"
  case ",$fail_samples," in
    *",$sample,"*) status="fail" ;;
  esac
  reads=$(( 100000 + ${#sample} * 137 ))
  printf '%s,%s,%s,12.5,92.0\n' "$sample" "$status" "$reads" >> "$outdir/qc/qc_summary.csv"
  printf 'fake fastqc report for %s\n' "$sample" > "$outdir/fastqc/${sample}_fastqc.txt"
  if command -v zip >/dev/null 2>&1; then
    (cd "$outdir/fastqc" && zip -q -j "${sample}_fastqc.zip" "${sample}_fastqc.txt") || true
  fi
done < "$samplesheet"

cat > "$outdir/multiqc_report.html" <<'HTML'
<html><head><title>Fake MultiQC</title></head><body><h1>Fake MultiQC report</h1></body></html>
HTML
echo "QC fixture complete: $(($(wc -l < "$outdir/qc/qc_summary.csv") - 1)) samples"
