# pipeline-qc-lims-test

Read-level QC pipeline used to exercise the platform's LIMS QC gate end to end.

## What it does

For every sample row of the input samplesheet, each column after the first is a
FASTQ location (local path, `s3://` key, or `http(s)://` URL). Files are streamed
once and their metrics summed per sample:

- `total_reads` — number of FASTQ records
- `q30` — percentage of bases with Phred score >= 30
- `gc` — percentage of G/C bases

Output: `<outdir>/qc/qc_summary.csv`

```csv
sample_id,total_reads,q30,gc
ERR044595,1000000,96.38,33.03
```

Pass/fail thresholds are deliberately **not** applied by the pipeline: the LIMS
pipeline config declares them as pass rules over the written-back metadata, e.g.
`qc.total_reads >= 100000` and `qc.q30 >= 90`.

## Inputs

| Env / param | Description |
| --- | --- |
| `input` | Samplesheet CSV, first column is the sample id, remaining columns are FASTQ files |
| `outdir` | Output directory (default `./outdir`) |
| `PYTHON` | Python 3 interpreter to use (default `python3`) |

Only the Python standard library is required. `s3://` inputs additionally need
`boto3` in the runtime environment; `http(s)://` inputs need no extra tooling.

## Test

```bash
python3 tests/test_qc.py
```
