#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Minimal timer around Chai-1 apptainer exec.")
    parser.add_argument("--fasta", default=str(Path.home() / "chai_in" / "query.fasta"), help="Path to input FASTA file")
    parser.add_argument("--sif-path", default=str(Path.home() / "chai_lab_x86.sif"), help="Path to Chai-1 SIF image")
    parser.add_argument("--in-dir", default=str(Path.home() / "chai_in"), help="Host input dir to bind to /in")
    parser.add_argument("--out-dir", default=str(Path.home() / "chai_out"), help="Host output dir to bind to /out")
    parser.add_argument("--run-name", default="run_" + datetime.now().strftime("%Y%m%d_%H%M%S"), help="Subfolder under /out for outputs")
    parser.add_argument("--use-esm", action="store_true", help="Use ESM embeddings (omit the --no-use-esm-embeddings flag)")
    args = parser.parse_args()

    # Pick runtime
    runtime = shutil.which("apptainer") or shutil.which("singularity")
    if not runtime:
        print("FATAL: apptainer/singularity not found on PATH", file=sys.stderr)
        sys.exit(1)

    # Ensure IO dirs
    in_dir = Path(args.in_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Stage FASTA as /in/query.fasta
    src = Path(args.fasta).expanduser().resolve()
    if not src.exists():
        print(f"FATAL: FASTA not found: {src}", file=sys.stderr)
        sys.exit(1)
    dst = in_dir / "query.fasta"
    if dst.exists():
        dst.unlink()
    shutil.copy2(str(src), str(dst))

    # Check SIF
    sif = Path(args.sif_path).expanduser().resolve()
    if not sif.exists():
        print(f"FATAL: SIF not found: {sif}", file=sys.stderr)
        sys.exit(1)

    # Build command
    cmd = [
        runtime, "exec", "--nv",
        "--bind", f"{in_dir}:/in,{out_dir}:/out",
        str(sif),
        "chai-lab", "fold",
    ]
    if not args.use_esm:
        cmd.append("--no-use-esm-embeddings")
    cmd += ["/in/query.fasta", f"/out/{args.run_name}"]

    print("Running:", " ".join(cmd))
    t0 = time.time()
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FATAL: command failed with return code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    t1 = time.time()
    elapsed = t1 - t0

    out_run_dir = out_dir / args.run_name
    print(f"Output directory: {out_run_dir}")
    if out_run_dir.exists():
        files = sorted(p.name for p in out_run_dir.iterdir())
        for name in files:
            print(" -", name)

    print(f"Elapsed seconds: {elapsed:.2f}")

if __name__ == "__main__":
    main()