"""Run experiments for the SHIR artifact.

This script assumes the Dockerfile has cloned the SHIR repo branches into

  /workspace/shir-routable-network-setup

For each run, it deletes `out/` before
running the test and then copies the freshly generated `out/` directory into
`results/<experiment-id>/lowering`.

Usage inside the container (from /workspace):

  python3 evaluation.py                 # run all experiments, both phases
  python3 evaluation.py --only 1-vgg,3-tinyyolo
"""

import argparse
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Dict, Set


WORKSPACE_DIR = "/workspace"
RESULTS_DIR = os.path.join(WORKSPACE_DIR, "results")


@dataclass
class PhaseConfig:
    branch: str
    # Scala test file path relative to the repo root
    path: str
    # If True, a non-zero exit code from sbt is treated as an expected failure.
    expect_failure: bool = False


@dataclass
class Experiment:
    """Description of one experiment (Lowering)."""

    id: str
    description: str
    lowering: Optional[PhaseConfig]
    figure: Optional[PhaseConfig]


def fqcn_from_test_path(path: str) -> str:
    """Derive the fully-qualified Scala test class name from a source path.

    Example:
      src/test/backend/hdl/arch/programmable/ConvTest#testVGGUnit16BitHalf.scala -> 
      backend.hdl.arch.programmable.ConvTest#testVGGUnit16BitHalf
    """

    # Strip leading src/test/ or src/test/scala/
    for prefix in ("src/test/scala/", "src/test/"):
        if path.startswith(prefix):
            path = path[len(prefix) :]
            break
    if path.endswith(".scala"):
        path = path[: -len(".scala")]
    return path.replace("/", ".")


def shir_repo_dir(branch: str) -> str:
    # Dockerfile clones into /workspace/shir-<branch>
    return os.path.join(WORKSPACE_DIR, f"shir-{branch}") 


def snapshot_files(root: str) -> Set[str]:
    """Return the set of relative file paths under root.

    We skip common build / VCS directories so we don't copy huge targets.
    """

    excluded_dirs = {".git", "target", "project", ".idea", ".bsp", ".metals"}
    files: Set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded dirs
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
        for fname in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fname), root)
            files.add(rel)
    return files


def copy_relative_paths(src_root: str, rel_paths: Set[str], dst_root: str) -> None:
    for rel in sorted(rel_paths):
        src = os.path.join(src_root, rel)
        dst = os.path.join(dst_root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def run_sbt_test(repo_dir: str, test_path: str, expect_failure: bool = False) -> None:
    fqcn = fqcn_from_test_path(test_path)
    print(f"\n==> Running sbt testOnly {fqcn} in {repo_dir}")
    cmd = [
        "sbt",
        "-J-Xss32m",
        f"testOnly {fqcn}",
    ]
    result = subprocess.run(cmd, cwd=repo_dir)
    if expect_failure:
        if result.returncode == 0:
            raise RuntimeError(
                f"[ERROR] Expected sbt testOnly {fqcn} to fail, but it succeeded."
            )
        else:
            print(
                f"[INFO] sbt testOnly {fqcn} failed as expected "
                f"(exit code {result.returncode})."
            )
    else:
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd)


def run_lowering_phase(exp: Experiment, cfg: PhaseConfig) -> None:
    repo = shir_repo_dir(cfg.branch)
    out_dir = os.path.join(repo, "out")
    print(f"\n==== Lowering phase: {exp.id} ({exp.description}) ====")

    # Clean previous lowering outputs to isolate this run.
    if os.path.exists(out_dir):
        print(f"Removing existing {out_dir} before run")
        shutil.rmtree(out_dir)

    run_sbt_test(repo, cfg.path)

    if not os.path.exists(out_dir):
        print("[WARN] Lowering phase did not produce an 'out' directory.")
        return

    dest = os.path.join(RESULTS_DIR, exp.id, "lowering")
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)

    # Find subdirectories inside out_dir
    subdirs = [
        d for d in os.listdir(out_dir)
        if os.path.isdir(os.path.join(out_dir, d))
    ]

    if not subdirs:
        raise RuntimeError(f"No subdirectories found in lowering output {out_dir}")
    elif len(subdirs) > 1:
        raise RuntimeError(f"Multiple subdirectories found in lowering output {out_dir}: {subdirs}")

    src_dir = os.path.join(out_dir, subdirs[0])
    print(f"Copying contents of {src_dir} to {dest}")

    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dest, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)


def recursive_chmod(path, mode):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), mode)
        for f in files:
            os.chmod(os.path.join(root, f), mode)
    os.chmod(path, mode)


EXPERIMENTS: List[Experiment] = [
    Experiment(
        id="expt-1",
        description="VGG16-Half",
        lowering=PhaseConfig(
            branch="routable-network-setup",
            path="src/test/backend/hdl/arch/programmable/testVGGUnit16BitHalf",
        ),
        figure=None,
    )
    Experiment(
        id="expt-2",
        description="VGG16-Full",
        lowering=PhaseConfig(
            branch="routable-network-setup",
            path="src/test/backend/hdl/arch/programmable/testVGGUnit16Bit",
        ),
        figure=None,
    ),
    Experiment(
        id="expt-3",
        description="TinyYolo-v2",
        lowering=PhaseConfig(
            branch="routable-network-setup",
            path="src/test/backend/hdl/arch/programmable/testTinyYoloV2Unit",
        ),
        figure=None,
    ),
    Experiment(
        id="expt-4",
        description="ResNet50-Quarter",
        lowering=PhaseConfig(
            branch="routable-network-setup",
            path="src/test/backend/hdl/arch/programmable/generateModelQuarter",
        ),
        figure=None,
    ),
    Experiment(
        id="expt-5",
        description="ResNet50-Third",
        lowering=PhaseConfig(
            branch="routable-network-setup",
            path="src/test/backend/hdl/arch/programmable/generateModelThird",
        ),
        figure=None,
    ),
    Experiment(
        id="expt-6",
        description="ResNet50-Half",
        lowering=PhaseConfig(
            branch="routable-network-setup",
            path="src/test/backend/hdl/arch/programmable/generateModelHalf",
        ),
        figure=None,
    ),
    Experiment(
        id="expt-7",
        description="ResNet50-Full",
        lowering=PhaseConfig(
            branch="routable-network-setup",
            path="src/test/backend/hdl/arch/programmable/generateModel",
        ),
        figure=None,
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SHIR  lowering experiments.")
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Comma-separated list of experiment IDs to run (default: all)",
    )
    parser.add_argument(
        "--phase",
        choices=["lowering"],
        default="lowering",
        help="The phases to run for each experiment.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        experiments = [e for e in EXPERIMENTS if e.id in wanted]
        unknown = wanted - {e.id for e in experiments}
        if unknown:
            print(f"[WARN] Unknown experiment IDs: {', '.join(sorted(unknown))}")
    else:
        experiments = EXPERIMENTS

    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f"Results will be stored under: {RESULTS_DIR}")

    s = os.path.join(WORKSPACE_DIR, 'scripts')
    d = os.path.join(RESULTS_DIR, 'scripts')
    if not os.path.isdir(d):
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    print(f"Copied script files to {RESULTS_DIR}")

    for exp in experiments:
        if args.phase in ("lowering", "both") and exp.lowering is not None:
            run_lowering_phase(exp, exp.lowering)
        elif args.phase in ("lowering", "both") and exp.lowering is None:
            print(f"\n==== Lowering phase: {exp.id} has no lowering configuration; skipping ====")

    recursive_chmod(RESULTS_DIR, 0o777)

if __name__ == "__main__":
    main()
