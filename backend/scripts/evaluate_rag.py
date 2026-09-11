"""
RAG evaluation harness (Phase 8)

Usage:
    python scripts/evaluate_rag.py

Workflow:
    1. Ask for K
    2. Evaluate retrieval
    3. Show retrieval report
    4. Ask whether to evaluate /chat
    5. Optionally evaluate /chat

Metrics:
    - Recall@K
    - Precision@K
    - MRR
    - Evidence-available accuracy
    - Citation correctness
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx


DATASET_PATH = Path(__file__).parent.parent / "eval" / "golden_dataset.json"


# -------------------------------------------------------------------
# SOURCE TITLE NORMALIZATION
# -------------------------------------------------------------------
#
# Your API currently returns:
#
#     "agriculture-12-00295-v2"
#
# while golden_dataset.json expects:
#
#     "Carbon Storage Potential of Agroforestry System near Brick Kilns"
#
# Add the other three document mappings here after checking their
# actual titles from /retrieve.
#
# Keys are API-returned titles.
# Values are golden-dataset titles.
#
SOURCE_TITLE_MAP = {
    "agriculture-12-00295-v2":
        "Carbon Storage Potential of Agroforestry System near Brick Kilns",
}


def normalize_title(title: str) -> str:
    """
    Convert an API/internal document title into the title used by
    golden_dataset.json.
    """
    if not title:
        return ""

    title = title.strip()

    # Exact mapping
    if title in SOURCE_TITLE_MAP:
        return SOURCE_TITLE_MAP[title]

    return title


def title_matches(expected_title: str, actual_title: str) -> bool:
    """
    Compare an expected golden-dataset title against an API title.
    """
    expected = normalize_title(expected_title).lower().strip()
    actual = normalize_title(actual_title).lower().strip()

    if not expected or not actual:
        return False

    return expected in actual or actual in expected


def get_unique_titles(
    sources: List[Dict[str, Any]],
    top_k: int,
) -> List[str]:
    """
    Return unique normalized source titles from top-K results.

    This prevents the same document being counted multiple times when
    several retrieved chunks belong to the same document.
    """
    titles = []

    for source in sources[:top_k]:
        title = normalize_title(source.get("title", ""))

        if title and title not in titles:
            titles.append(title)

    return titles


# -------------------------------------------------------------------
# RETRIEVAL EVALUATION
# -------------------------------------------------------------------

def evaluate_retrieval(
    item: Dict[str, Any],
    sources: List[Dict[str, Any]],
    top_k: int,
) -> Dict[str, Any]:

    expected = item["expected_source_titles"]

    # Q29/Q30 etc.
    if not expected:
        return {
            "recall_at_k": None,
            "precision_at_k": None,
            "reciprocal_rank": None,
            "retrieved_titles": get_unique_titles(sources, top_k),
            "expected_titles": [],
        }

    retrieved_titles = get_unique_titles(sources, top_k)

    # ---------------------------------------------------------------
    # Recall
    # ---------------------------------------------------------------
    #
    # For every expected source, check whether it was retrieved.
    #
    hits = [
        any(
            title_matches(expected_title, retrieved_title)
            for retrieved_title in retrieved_titles
        )
        for expected_title in expected
    ]

    recall_at_k = sum(hits) / len(expected)

    # ---------------------------------------------------------------
    # Precision
    # ---------------------------------------------------------------
    #
    # Count unique retrieved documents that are relevant.
    #
    relevant_retrieved = sum(
        1
        for retrieved_title in retrieved_titles
        if any(
            title_matches(expected_title, retrieved_title)
            for expected_title in expected
        )
    )

    precision_at_k = (
        relevant_retrieved / len(retrieved_titles)
        if retrieved_titles
        else 0.0
    )

    # ---------------------------------------------------------------
    # MRR
    # ---------------------------------------------------------------
    #
    # MRR should use the ranking of unique documents.
    #
    reciprocal_rank = 0.0

    for rank, retrieved_title in enumerate(
        retrieved_titles,
        start=1,
    ):
        if any(
            title_matches(expected_title, retrieved_title)
            for expected_title in expected
        ):
            reciprocal_rank = 1 / rank
            break

    return {
        "recall_at_k": recall_at_k,
        "precision_at_k": precision_at_k,
        "reciprocal_rank": reciprocal_rank,
        "retrieved_titles": retrieved_titles,
        "expected_titles": expected,
    }


# -------------------------------------------------------------------
# CITATION EVALUATION
# -------------------------------------------------------------------

def evaluate_citation_correctness(
    item: Dict[str, Any],
    chat_sources: List[Dict[str, Any]],
) -> bool:

    expected = item["expected_source_titles"]

    # For intentionally unanswerable questions, no sources should
    # normally be cited.
    if not expected:
        return len(chat_sources) == 0

    return any(
        title_matches(
            expected_title,
            source.get("title", ""),
        )
        for expected_title in expected
        for source in chat_sources
    )


# -------------------------------------------------------------------
# CHAT
# -------------------------------------------------------------------

def chat_with_retry(
    client: httpx.Client,
    query: str,
    max_retries: int = 1,
) -> httpx.Response:

    for attempt in range(max_retries + 1):

        response = client.post(
            "/chat",
            json={"query": query},
        )

        # Success
        if response.status_code < 400:
            return response

        # -----------------------------------------------------------
        # 429
        # -----------------------------------------------------------
        if response.status_code == 429:

            if attempt == max_retries:
                return response

            retry_after = response.headers.get("Retry-After")

            try:
                wait_time = int(retry_after) if retry_after else 10
            except ValueError:
                wait_time = 10

            print(
                f"      429 Too Many Requests. "
                f"Waiting {wait_time}s..."
            )

            time.sleep(wait_time)
            continue

        # -----------------------------------------------------------
        # 503
        # -----------------------------------------------------------
        #
        # A 503 is usually a backend/dependency problem rather than
        # a client rate-limit problem. We don't want to wait 5 seconds
        # three or four times for every question.
        #
        if response.status_code == 503:

            if attempt == max_retries:
                return response

            print(
                "      503 Service Unavailable. "
                "Retrying once in 3s..."
            )

            time.sleep(3)
            continue

        # Other errors
        return response

    return response


# -------------------------------------------------------------------
# MAIN RUNNER
# -------------------------------------------------------------------

def run(
    base_url: str,
    top_k: int,
    run_chat: bool,
) -> None:

    dataset = json.loads(
        DATASET_PATH.read_text(encoding="utf-8")
    )

    items = dataset["items"]

    results = []

    # Used to display API metadata problems only once.
    seen_raw_titles = set()

    with httpx.Client(
        base_url=base_url,
        timeout=60.0,
    ) as client:

        # ===========================================================
        # RETRIEVAL EVALUATION
        # ===========================================================

        print()
        print("=" * 70)
        print(f"RETRIEVAL EVALUATION — K={top_k}")
        print("=" * 70)

        for item in items:

            print(
                f"\n  {item['id']}: "
                f"{item['query'][:70]}..."
            )

            try:

                retrieve_resp = client.post(
                    "/retrieve",
                    json={
                        "query": item["query"],
                        "top_k": top_k,
                    },
                )

                retrieve_resp.raise_for_status()

                retrieve_data = retrieve_resp.json()

                sources = retrieve_data.get("sources", [])

                # ---------------------------------------------------
                # Display raw source titles returned by API
                # ---------------------------------------------------

                for source in sources[:top_k]:

                    raw_title = source.get("title", "")

                    if raw_title and raw_title not in seen_raw_titles:

                        seen_raw_titles.add(raw_title)

                        normalized = normalize_title(raw_title)

                        if normalized != raw_title:

                            print(
                                f"      Source mapping: "
                                f"{raw_title} "
                                f"-> "
                                f"{normalized}"
                            )

                        else:

                            print(
                                f"      Source returned by API: "
                                f"{raw_title}"
                            )

                # ---------------------------------------------------
                # Evaluate
                # ---------------------------------------------------

                retrieval_metrics = evaluate_retrieval(
                    item,
                    sources,
                    top_k,
                )

                results.append(
                    {
                        "id": item["id"],
                        "category": item["category"],
                        **retrieval_metrics,
                        "evidence_available_correct": None,
                        "citation_correct": None,
                        "actual_evidence_available": None,
                        "expected_evidence_available":
                            item["expected_evidence_available"],
                    }
                )

            except httpx.HTTPStatusError as e:

                print(
                    f"      Retrieve error: "
                    f"HTTP {e.response.status_code}"
                )

            except Exception as e:

                print(
                    f"      Retrieve error: {e}"
                )

        # ===========================================================
        # RETRIEVAL REPORT
        # ===========================================================

        _print_report(
            results,
            include_chat=False,
        )

        # ===========================================================
        # ASK WHETHER TO RUN CHAT
        # ===========================================================

        if not run_chat:

            print("\nChat evaluation skipped.")
            return

        # ===========================================================
        # CHAT EVALUATION
        # ===========================================================

        print()
        print("=" * 70)
        print("CHAT EVALUATION")
        print("=" * 70)

        for index, item in enumerate(items):

            print(
                f"\n  {item['id']}: "
                f"{item['query'][:70]}..."
            )

            try:

                chat_resp = chat_with_retry(
                    client,
                    item["query"],
                )

                if chat_resp.status_code == 503:

                    print(
                        "      Chat unavailable (HTTP 503). "
                        "Skipping this question."
                    )

                    continue

                chat_resp.raise_for_status()

                chat_data = chat_resp.json()

                # ---------------------------------------------------
                # Evidence correctness
                # ---------------------------------------------------

                evidence_correct = (
                    chat_data.get("evidence_available")
                    == item["expected_evidence_available"]
                )

                # ---------------------------------------------------
                # Citation correctness
                # ---------------------------------------------------

                citation_correct = (
                    evaluate_citation_correctness(
                        item,
                        chat_data.get("sources", []),
                    )
                )

                # ---------------------------------------------------
                # Update corresponding retrieval result
                # ---------------------------------------------------

                result = next(
                    (
                        r
                        for r in results
                        if r["id"] == item["id"]
                    ),
                    None,
                )

                if result:

                    result["evidence_available_correct"] = (
                        evidence_correct
                    )

                    result["citation_correct"] = (
                        citation_correct
                    )

                    result["actual_evidence_available"] = (
                        chat_data.get("evidence_available")
                    )

                # Prevent rate limiting
                if index < len(items) - 1:
                    time.sleep(2)

            except httpx.HTTPStatusError as e:

                print(
                    f"      Chat error: "
                    f"HTTP {e.response.status_code}"
                )

            except Exception as e:

                print(
                    f"      Chat error: {e}"
                )

        # ===========================================================
        # FINAL REPORT
        # ===========================================================

        _print_report(
            results,
            include_chat=True,
        )


# -------------------------------------------------------------------
# REPORT
# -------------------------------------------------------------------

def _print_report(
    results: List[Dict[str, Any]],
    include_chat: bool = True,
) -> None:

    answerable = [
        r
        for r in results
        if r["recall_at_k"] is not None
    ]

    unanswerable = [
        r
        for r in results
        if r["recall_at_k"] is None
    ]

    def avg(
        key: str,
        rows: List[Dict[str, Any]],
    ) -> float:

        vals = [
            r[key]
            for r in rows
            if r[key] is not None
        ]

        return (
            sum(vals) / len(vals)
            if vals
            else 0.0
        )

    print("\n" + "=" * 70)
    print("RAG EVALUATION REPORT")
    print("=" * 70)

    print(
        f"Total questions: {len(results)} "
        f"(answerable: {len(answerable)}, "
        f"unanswerable: {len(unanswerable)})"
    )

    print()
    print("--- Retrieval quality ---")

    print(
        f"  Recall@K:    "
        f"{avg('recall_at_k', answerable):.2%}"
    )

    print(
        f"  Precision@K: "
        f"{avg('precision_at_k', answerable):.2%}"
    )

    print(
        f"  MRR:         "
        f"{avg('reciprocal_rank', answerable):.3f}"
    )

    # ---------------------------------------------------------------
    # Per-question retrieval details
    # ---------------------------------------------------------------

    print()
    print("--- Per-question retrieval ---")

    for result in results:

        if result["recall_at_k"] is None:
            print(
                f"  {result['id']}: "
                f"unanswerable / no expected source"
            )
            continue

        print(
            f"  {result['id']}: "
            f"Recall={result['recall_at_k']:.0%}, "
            f"Precision={result['precision_at_k']:.0%}, "
            f"RR={result['reciprocal_rank']:.3f}"
        )

        print(
            f"      Expected: "
            f"{result['expected_titles']}"
        )

        print(
            f"      Retrieved: "
            f"{result['retrieved_titles']}"
        )

    # ---------------------------------------------------------------
    # Chat
    # ---------------------------------------------------------------

    if include_chat:

        chat_results = [
            r
            for r in results
            if r["evidence_available_correct"] is not None
        ]

        if chat_results:

            print()
            print("--- Chat correctness ---")

            evidence_acc = (
                sum(
                    r["evidence_available_correct"]
                    for r in chat_results
                )
                / len(chat_results)
            )

            citation_acc = (
                sum(
                    r["citation_correct"]
                    for r in chat_results
                )
                / len(chat_results)
            )

            print(
                f"  Evidence-available accuracy: "
                f"{evidence_acc:.2%}"
            )

            print(
                f"  Citation correctness:         "
                f"{citation_acc:.2%}"
            )

            failures = [
                r
                for r in chat_results
                if not r["evidence_available_correct"]
                or not r["citation_correct"]
            ]

            if failures:

                print()
                print("--- Chat failures ---")

                for r in failures:

                    citation_msg = (
                        ""
                        if r["citation_correct"]
                        else " | citation mismatch"
                    )

                    print(
                        f"  {r['id']} ({r['category']}): "
                        f"expected "
                        f"evidence_available="
                        f"{r['expected_evidence_available']}, "
                        f"got "
                        f"{r['actual_evidence_available']}"
                        f"{citation_msg}"
                    )

            else:

                print()
                print("No chat failures.")

        else:

            print()
            print(
                "No successful /chat responses to evaluate."
            )

    print("=" * 70)


# -------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base-url",
        default="http://localhost:8000/api",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--chat",
        action="store_true",
        help="Run /chat evaluation after retrieval.",
    )

    args = parser.parse_args()

    if not DATASET_PATH.exists():

        print(
            f"Golden dataset not found at "
            f"{DATASET_PATH}",
            file=sys.stderr,
        )

        sys.exit(1)

    # ===============================================================
    # ASK K
    # ===============================================================

    if args.top_k is None:

        while True:

            try:

                top_k = int(
                    input(
                        "\nEnter K value "
                        "(1, 3, 5, 10): "
                    )
                )

                if top_k > 0:
                    break

                print("K must be greater than 0.")

            except ValueError:

                print("Please enter a valid number.")

    else:

        top_k = args.top_k

    # ===============================================================
    # RUN RETRIEVAL FIRST
    # ===============================================================

    run_chat = args.chat

    run(
        args.base_url,
        top_k,
        run_chat,
    )