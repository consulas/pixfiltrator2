#!/usr/bin/env python3
"""
Script: create_patch.py
Usage: python3 create_patch.py /path/to/repo /path/to/output.patch [--from-commit HASH]
Description:
  Create a git patch from the beginning of a repo's history (or from a given commit).
  Defaults to diffing from the empty tree so all commits are included.
"""

import os
import sys
import argparse
import subprocess

EMPTY_TREE_HASH = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
DEFAULT_OUTPUT_PATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.patch")


def main():
    parser = argparse.ArgumentParser(description="Create a git patch from a repository.")
    parser.add_argument("repo_path", help="Path to the source git repository")
    parser.add_argument(
        "output_patch",
        nargs="?",
        default=DEFAULT_OUTPUT_PATCH,
        help=f"Path to write the output patch file (default: {DEFAULT_OUTPUT_PATCH})",
    )
    parser.add_argument(
        "--from-commit",
        default=EMPTY_TREE_HASH,
        help=f"Starting commit hash (default: empty tree {EMPTY_TREE_HASH})",
    )
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo_path)
    output_patch = os.path.abspath(args.output_patch)

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        sys.exit(f"Error: {repo_path} is not a git repository.")

    result = subprocess.run(
        ["git", "diff", "--binary", args.from_commit, "HEAD"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        sys.exit(f"Error creating patch: {result.stderr.strip()}")

    if not result.stdout:
        sys.exit("No changes found — patch would be empty.")

    with open(output_patch, "w") as f:
        f.write(result.stdout)

    print(f"Patch written to {output_patch}")


if __name__ == "__main__":
    main()
