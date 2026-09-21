#!/usr/bin/env python3
"""Smoke test for the FASTQ QC engine: python3 tests/test_qc.py"""

import gzip
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from omicslab.qc import FastqMetrics, main, measure  # noqa: E402


def _write_fastq(path: str, records: list[tuple[str, str]]) -> None:
    with gzip.open(path, "wt") as handle:
        for index, (sequence, quality) in enumerate(records):
            handle.write(f"@read{index}\n{sequence}\n+\n{quality}\n")


def test_measure_counts_reads_q30_and_gc() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "reads.fastq.gz")
        # 2 reads: quality "IIII" (Q40) and "!!!!" (Q0) -> q30 = 50%.
        # bases: ACGT + AATT -> GC = 2/8 = 25%.
        _write_fastq(path, [("ACGT", "IIII"), ("AATT", "!!!!")])
        metrics = measure(path)
        assert metrics.reads == 2, metrics
        assert metrics.bases == 8, metrics
        assert metrics.q30 == 50.0, metrics
        assert metrics.gc == 25.0, metrics
        assert FastqMetrics().q30 == 0.0


def test_main_writes_summary_and_sums_files_per_sample() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r1 = os.path.join(tmp, "S1_R1.fastq.gz")
        r2 = os.path.join(tmp, "S1_R2.fastq.gz")
        _write_fastq(r1, [("GGGG", "IIII")])
        _write_fastq(r2, [("CCCC", "IIII")])
        samplesheet = os.path.join(tmp, "samplesheet.csv")
        with open(samplesheet, "w") as handle:
            handle.write(f"sample,fastq_1,fastq_2\nS1,{r1},{r2}\n")
        outdir = os.path.join(tmp, "out")
        assert main(["qc.py", samplesheet, outdir]) == 0
        with open(os.path.join(outdir, "qc", "qc_summary.csv")) as handle:
            rows = handle.read().strip().splitlines()
        assert rows[0] == "sample_id,total_reads,q30,gc", rows
        assert rows[1] == "S1,2,100.0,100.0", rows


if __name__ == "__main__":
    test_measure_counts_reads_q30_and_gc()
    test_main_writes_summary_and_sums_files_per_sample()
    print("ok")
