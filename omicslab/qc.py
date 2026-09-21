#!/usr/bin/env python3
"""Read-level QC for FASTQ files listed in a samplesheet.

For every sample row the columns after the first hold FASTQ locations (local
paths, ``s3://`` keys, or ``http(s)://`` URLs). Each file is streamed once and
the sample's metrics are the sum over its files:

- ``total_reads``: number of FASTQ records
- ``q30``: percentage of bases with Phred score >= 30
- ``gc``: percentage of G/C bases

The output is ``<outdir>/qc/qc_summary.csv`` with one row per sample. Pass/fail
thresholds are intentionally not applied here: the platform's QC gate evaluates
them against the run's configured pass rules.
"""

from __future__ import annotations

import csv
import gzip
import io
import os
import sys
import urllib.request
from dataclasses import dataclass
from typing import BinaryIO, Iterator


class QCError(RuntimeError):
    """Raised when a samplesheet or FASTQ file cannot be read."""


@dataclass
class FastqMetrics:
    reads: int = 0
    bases: int = 0
    q30_bases: int = 0
    gc_bases: int = 0

    def add(self, other: "FastqMetrics") -> None:
        self.reads += other.reads
        self.bases += other.bases
        self.q30_bases += other.q30_bases
        self.gc_bases += other.gc_bases

    @property
    def q30(self) -> float:
        return round(100.0 * self.q30_bases / self.bases, 2) if self.bases else 0.0

    @property
    def gc(self) -> float:
        return round(100.0 * self.gc_bases / self.bases, 2) if self.bases else 0.0


def _open_local(path: str) -> BinaryIO:
    return gzip.open(path, "rb") if path.endswith(".gz") else open(path, "rb")


def _open_remote(url: str) -> BinaryIO:
    response = urllib.request.urlopen(url)
    if url.endswith(".gz"):
        return gzip.GzipFile(fileobj=response)
    return response


def _open_s3(key: str) -> BinaryIO:
    try:
        import boto3  # type: ignore[import-not-found]
    except ImportError:
        boto3 = None
    if boto3 is not None:
        bucket, _, obj = key[len("s3://") :].partition("/")
        body = boto3.client("s3").get_object(Bucket=bucket, Key=obj)["Body"]
        stream = body._raw_stream if hasattr(body, "_raw_stream") else body
        return gzip.GzipFile(fileobj=stream) if key.endswith(".gz") else stream
    raise QCError(f"cannot read {key}: boto3 is not installed")


def open_fastq(location: str) -> BinaryIO:
    if location.startswith("s3://"):
        return _open_s3(location)
    if location.startswith(("http://", "https://")):
        return _open_remote(location)
    if not os.path.exists(location):
        raise QCError(f"FASTQ file not found: {location}")
    return _open_local(location)


def records(handle: BinaryIO) -> Iterator[tuple[str, str]]:
    """Yield ``(sequence, quality)`` for every FASTQ record in the stream."""
    text = io.TextIOWrapper(handle, encoding="ascii", errors="replace", newline="")
    while True:
        header = text.readline()
        if not header:
            return
        sequence = text.readline()
        text.readline()  # '+' separator
        quality = text.readline()
        if not quality:
            raise QCError("truncated FASTQ record")
        yield sequence.strip().upper(), quality.strip()


def measure(location: str) -> FastqMetrics:
    metrics = FastqMetrics()
    with open_fastq(location) as handle:
        for sequence, quality in records(handle):
            if len(sequence) != len(quality):
                raise QCError(f"sequence/quality length mismatch in {location}")
            metrics.reads += 1
            metrics.bases += len(sequence)
            metrics.gc_bases += sequence.count("G") + sequence.count("C")
            metrics.q30_bases += sum(1 for char in quality if ord(char) - 33 >= 30)
    return metrics


def read_samplesheet(path: str) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    with open(path, newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            raise QCError(f"samplesheet is empty: {path}") from None
        if len(header) < 2:
            raise QCError(f"samplesheet needs a sample column and at least one FASTQ column: {path}")
        for line in reader:
            if not line or not line[0].strip():
                continue
            rows.append((line[0].strip(), [cell.strip() for cell in line[1:] if cell.strip()]))
    if not rows:
        raise QCError(f"samplesheet has no sample rows: {path}")
    return rows


def main(argv: list[str]) -> int:
    samplesheet = argv[1] if len(argv) > 1 else os.environ.get("input", "")
    outdir = argv[2] if len(argv) > 2 else os.environ.get("outdir", "./outdir")
    if not samplesheet or not os.path.exists(samplesheet):
        print(f"qc: missing samplesheet: {samplesheet}", file=sys.stderr)
        return 1

    rows = read_samplesheet(samplesheet)
    qc_dir = os.path.join(outdir, "qc")
    os.makedirs(qc_dir, exist_ok=True)
    summary_path = os.path.join(qc_dir, "qc_summary.csv")

    with open(summary_path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample_id", "total_reads", "q30", "gc"])
        for sample_id, files in rows:
            metrics = FastqMetrics()
            for location in files:
                metrics.add(measure(location))
            writer.writerow([sample_id, metrics.reads, metrics.q30, metrics.gc])
            print(
                f"qc: {sample_id} reads={metrics.reads} q30={metrics.q30} gc={metrics.gc}",
                flush=True,
            )

    print(f"qc: wrote {summary_path} ({len(rows)} samples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
