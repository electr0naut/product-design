#!/usr/bin/env python3
"""Generate a phase-04 PRD from an approved BRD."""

from __future__ import annotations

import argparse

from gate_reviews import add_review_args, maybe_enforce_gate, verify_bundle
from split_prd import split_content
from workflow_common import (
    FALLBACK,
    PROMPT_SUFFIX,
    PROMPTS,
    ROOT,
    add_common_args,
    attach_review,
    bundle_documents,
    compose_prompt,
    exit_status,
    generate,
    project_path,
    reject_symlink,
    run_claude,
    slug_from_path,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brd", required=True, help="Path to the approved BRD.")
    parser.add_argument("--out", help="Output PRD path.")
    parser.add_argument("--format", choices=("single", "split"), default="single")
    add_common_args(parser)
    add_review_args(parser)
    args = parser.parse_args()

    brd = project_path(args.brd)
    default_out = (
        ROOT / "04-prd" / slug_from_path(brd)
        if args.format == "split"
        else ROOT / "04-prd" / f"{slug_from_path(brd)}-prd.md"
    )
    output = project_path(args.out) if args.out else default_out
    statuses = maybe_enforce_gate(
        args,
        slug_from_path(brd),
        "brd-to-prd",
        [brd],
        output_product=slug_from_path(output),
        search_from=output,
    )
    context = bundle_documents("BRD", [brd])
    verify_bundle(context, statuses)
    prompt = compose_prompt(
        PROMPTS / "04-generate-prd.md",
        ROOT / "04-prd" / "templates" / "prd-template.md",
        context,
    )
    attach_review(prompt, statuses["review"] if statuses and args.format == "split" else None)
    if args.format == "split":
        reject_symlink(output, "split PRD output")
        if output.exists() and not args.force:
            raise SystemExit(f"Split PRD output already exists: {output} (use --force).")
        if args.prompt_only:
            exit_status(
                [generate(prompt, output / "prd.prompt.md", True, args.claude_bin, args.force)]
            )
            return
        response = run_claude(prompt, args.claude_bin, output / "prd.prompt.md", args.force)
        if response is None:
            exit_status([FALLBACK])
            return
        try:
            files = split_content(response)
        except ValueError as exc:
            raise SystemExit(f"Invalid generated PRD; no artifacts written: {exc}") from exc
        for relative in files:
            target = output / relative
            sidecar = target.with_suffix(".provenance.json")
            for path in (target, sidecar):
                reject_symlink(path, "split PRD artifact")
                if path.exists() and not args.force:
                    raise SystemExit(f"Split PRD artifact already exists: {path} (use --force).")
        exit_status(
            [
                generate(
                    prompt,
                    output / relative,
                    False,
                    args.claude_bin,
                    args.force,
                    content_override=content,
                )
                for relative, content in files.items()
            ]
        )
        return
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    exit_status([generate(prompt, output, args.prompt_only, args.claude_bin, args.force)])


if __name__ == "__main__":
    main()
