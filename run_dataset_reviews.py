#!/usr/bin/env python3
"""
Run AST-Reviewer across a dataset by mapping entries to cached repositories.

Example:
    python run_dataset_reviews.py \
        ../origin_dataset/Python-22k/Python-22k/valid.json \
        --repo-cache ../repo_cache \
        --output runs/valid_predictions_lora.jsonl \
        --resume \
        --lora ../gemma4b-lora-python \
        --no-retrieval
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

from ast_reviewer.agents.experts import CommentConsistencyExpert
from ast_reviewer.retrieval.cast.pipeline import CASTChunker
from ast_reviewer.retrieval.vector_store import VectorStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch review dataset samples.")
    parser.add_argument(
        "dataset",
        help="Path to the dataset JSON file (list of samples).",
    )
    parser.add_argument(
        "--repo-cache",
        default="repo_cache",
        help="Root directory containing <owner>/<repo>/<commit> checkouts.",
    )
    parser.add_argument(
        "--output",
        default="dataset_reviews.jsonl",
        help="Path to output JSONL file with added expert/model outputs.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing output file instead of overwriting.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of samples to process.",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Optional starting index within the dataset.",
    )
    parser.add_argument(
        "--no-retrieval",
        action="store_true",
        help="Disable retrieval and run experts on raw code only.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of context chunks to retrieve per sample (default: 3).",
    )
    parser.add_argument(
        "--lora",
        type=str,
        default=None,
        help="Optional path to LoRA adapters for experts.",
    )
    return parser.parse_args()


def repo_slug(repo_url: str) -> str:
    slug = repo_url.split("github.com/")[-1].rstrip("/")
    if slug.endswith(".git"):
        slug = slug[:-4]
    return slug


def sanitize(name: str) -> str:
    return name.replace("/", "__").replace(".", "_")


def index_file(file_path: Path, collection_name: str, chunker: CASTChunker) -> VectorStore:
    store = VectorStore(collection_name=collection_name)
    store.clear()
    try:
        chunks = chunker.chunk_file(str(file_path))
        store.add_chunks(chunks)
    except Exception as exc:
        print(f"[warn] Failed to chunk {file_path}: {exc}", file=sys.stderr)
    return store


def get_vector_store(
    cache: Dict[str, VectorStore],
    target_file: Path,
    use_retrieval: bool,
    chunker: CASTChunker,
) -> Optional[VectorStore]:
    if not use_retrieval:
        return None
    if not target_file or not target_file.exists():
        return None

    key = str(target_file.resolve())
    if key in cache:
        return cache[key]

    collection_name = f"file_{sanitize(key)}"
    print(f"[index] Building vector store for {target_file}")
    cache[key] = index_file(target_file, collection_name=collection_name, chunker=chunker)
    return cache[key]


def load_dataset(path: str, start: int, limit: Optional[int]) -> List[Dict]:
    data = json.load(open(path, "r"))
    if not isinstance(data, list):
        raise ValueError("Dataset must be a list of samples.")
    sliced = data[start:]
    if limit is not None:
        sliced = sliced[:limit]
    return sliced


def sample_key(sample: Dict) -> str:
    """Generate a unique key for a dataset sample."""
    if sample.get("id"):
        return str(sample["id"])
    return "|".join([
        sample.get("repo_url", ""),
        sample.get("commit", ""),
        sample.get("path", "")
    ])


def load_processed_keys(output_path: Path) -> Set[str]:
    processed: Set[str] = set()
    if not output_path.exists():
        return processed
    with output_path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = sample_key(record)
            if key:
                processed.add(key)
    return processed


def build_review_input(sample: Dict) -> str:
    sections = []
    def add_section(title: str, content: str) -> None:
        if content:
            sections.append(f"### {title}\n{content.strip()}")

    add_section("Old Code", sample.get("old_code_raw", ""))
    add_section("New Code", sample.get("new_code_raw", ""))
    add_section("Existing Comment", sample.get("old_comment_raw", ""))
    add_section("New Comment", sample.get("new_comment_raw", ""))
    return "\n\n".join(sections)


def review_sample(
    sample: Dict,
    target_path: Optional[Path],
    store: Optional[VectorStore],
    experts: List,
    top_k: int,
) -> Dict:
    code_content = build_review_input(sample)

    retrieved = []
    if store:
        retrieved = store.query(code_content[:1000], n_results=top_k)

    expert_output: Dict[str, List[str]] = {}
    model_output: Dict[str, int] = {}
    for expert in experts:
        comments = expert.review(code_content, retrieved)
        expert_output[expert.name] = comments
        model_output[expert.name] = 1 if comments else 0

    result = dict(sample)
    result["file_path"] = str(target_path) if target_path else None
    result["expert_output"] = expert_output
    result["model_output"] = model_output
    result["model_input"] = code_content
    return result


def main() -> None:
    args = parse_args()
    repo_cache_root = Path(args.repo_cache).resolve()
    if not repo_cache_root.exists():
        raise FileNotFoundError(f"Repo cache root not found: {repo_cache_root}")

    dataset = load_dataset(args.dataset, args.start, args.limit)
    print(f"Loaded {len(dataset)} samples to review.")

    chunker = CASTChunker()
    experts = [
        CommentConsistencyExpert(lora_path=args.lora),
    ]
    store_cache: Dict[str, VectorStore] = {}

    output_path = Path(args.output)
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    if args.resume:
        processed_keys = load_processed_keys(output_path)
        write_mode = "a"
        if processed_keys:
            print(f"Resuming from {output_path}, found {len(processed_keys)} processed samples.")
    else:
        processed_keys = set()
        write_mode = "w"
    processed = 0
    with open(output_path, write_mode) as fout:
        for idx, sample in enumerate(dataset, start=args.start):
            repo_url = sample.get("repo_url")
            commit = sample.get("commit")
            if not repo_url or not commit:
                print(f"[skip] sample {idx} missing repo_url/commit", file=sys.stderr)
                continue

            slug = repo_slug(repo_url)
            repo_root = repo_cache_root / slug / commit
            if not repo_root.exists():
                print(f"[skip] repo not cached for sample {idx}: {repo_root}", file=sys.stderr)
                continue

            target_rel = sample.get("path")
            if not target_rel:
                print(f"[skip] sample {idx} missing file path.", file=sys.stderr)
                continue
            key = sample_key(sample)
            if key in processed_keys:
                print(f"[skip] sample {idx} already processed ({key}).")
                continue

            target_path = repo_root / target_rel
            if not target_path.exists():
                print(f"[skip] file not found for sample {idx}: {target_path}", file=sys.stderr)
                continue

            print(f"[{processed+1}] Reviewing {slug}@{commit} :: {target_rel}")
            store = get_vector_store(store_cache, target_path, not args.no_retrieval, chunker)
            try:
                record = review_sample(sample, target_path, store, experts, args.top_k)
            except Exception as exc:
                print(f"[error] sample {idx} failed: {exc}", file=sys.stderr)
                continue

            fout.write(json.dumps(record) + "\n")
            processed_keys.add(key)
            processed += 1

    print(f"Completed {processed} samples. Results written to {args.output}")


if __name__ == "__main__":
    main()
