"""Compare three S3 Vectors query modes on the same Japanese FAQ index."""

import argparse
import json
import math
import re
import sys
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from statistics import median
from time import perf_counter, sleep
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, HTTPClientError, IncompleteReadError
from botocore.exceptions import ConnectionError as AWSConnectionError
from botocore.parsers import ResponseParserError

from fixtures import QUERIES, documents

REGION = "ap-northeast-1"
JST = timezone(timedelta(hours=9))
INDEX_NAME = "faq"
MODEL = "intfloat/multilingual-e5-small"
MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
DIMENSION = 384
MODES = ("全文", "ベクトル", "ハイブリッド")
TOP_K = 5
MAX_QUERIES = 300
MAX_LOGICAL_BYTES = 256 * 1024
RESULTS = Path(__file__).resolve().parent / "results"
AMBIGUOUS_CREATE_ERRORS = {
    "RequestTimeoutException",
    "InternalServerException",
    "ServiceUnavailableException",
}
AMBIGUOUS_HTTP_STATUSES = {408, 500, 502, 503, 504}
CREATE_LOOKUP_DELAYS = (0, 1, 2)
AWS_REQUEST_ERRORS = (
    ClientError,
    AWSConnectionError,
    HTTPClientError,
    IncompleteReadError,
    ResponseParserError,
    UnicodeError,
    json.JSONDecodeError,
)


def validate_fixtures(corpus, queries):
    keys = {doc.key for doc in corpus}
    counts = Counter(query.group for query in queries)
    if len(corpus) != 100 or len(keys) != 100:
        raise ValueError("FAQ must have 100 unique keys")
    if counts != {"型番": 5, "言い換え": 5, "混合": 5} or len({q.text for q in queries}) != len(queries):
        raise ValueError("Expected five distinct queries in each group")
    for query in queries:
        if not query.expected_keys or not set(query.expected_keys) <= keys:
            raise ValueError(f"Invalid relevance judgment for {query.text}")


def embed(corpus, queries):
    try:
        from sentence_transformers import SentenceTransformer
    except ModuleNotFoundError as error:
        if error.name != "sentence_transformers":
            raise
        raise RuntimeError("Run with: uv run --locked --extra embedding experiment.py") from error

    model = SentenceTransformer(MODEL, revision=MODEL_REVISION, device="cpu")
    vectors = model.encode(
        [f"passage: {doc.body}" for doc in corpus] + [f"query: {query.text}" for query in queries],
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()
    for vector in vectors:
        if len(vector) != DIMENSION or not all(math.isfinite(value) for value in vector):
            raise ValueError("Expected finite 384-dimensional embeddings")
    return vectors[: len(corpus)], vectors[len(corpus) :]


def index_options(bucket_arn):
    return {
        "vectorBucketArn": bucket_arn,
        "indexName": INDEX_NAME,
        "dataType": "float32",
        "dimension": DIMENSION,
        "distanceMetric": "cosine",
        "metadataConfiguration": {
            "nonFilterableMetadataKeys": ["body"],
            "textSearchConfigurations": [{"metadataKey": "body", "language": "ja"}],
        },
    }


def prepare_batch(corpus, passage_vectors):
    batch = [
        {
            "key": doc.key,
            "data": {"float32": vector},
            "metadata": {"body": doc.body, "category": doc.category},
        }
        for doc, vector in zip(corpus, passage_vectors, strict=True)
    ]
    # JSON encoding includes metadata field names and punctuation, so the estimate is conservative.
    logical_bytes = sum(
        DIMENSION * 4 + len(item["key"].encode())
        + len(json.dumps(item["metadata"], ensure_ascii=False).encode())
        for item in batch
    )
    if logical_bytes > MAX_LOGICAL_BYTES:
        raise ValueError(f"PUT estimate exceeds {MAX_LOGICAL_BYTES} bytes")
    return batch, logical_bytes


def query_options(index_arn, mode, query, vector, category=None):
    options = {"indexArn": index_arn, "topK": TOP_K}
    if mode in ("全文", "ハイブリッド"):
        options["queryTexts"] = [{"metadataKey": "body", "text": query.text}]
        options["returnScores"] = True
    if mode in ("ベクトル", "ハイブリッド"):
        options["queryVector"] = {"float32": vector}
    if mode == "ベクトル":
        options["returnDistance"] = True
    if category:
        options["filter"] = {"category": {"$eq": category}}
    return options


def call_query(client, options):
    start = perf_counter()
    response = client.query_vectors(**options)
    elapsed_ms = (perf_counter() - start) * 1000
    return response["vectors"], round(elapsed_ms, 3)


def measure(client, index_arn, queries, query_vectors, repeats):
    rows = []
    for repeat in range(repeats):
        for case_number, (query, vector) in enumerate(zip(queries, query_vectors, strict=True)):
            # Rotate the first mode to avoid consistently giving it a fresh connection or cache.
            offset = (repeat + case_number) % len(MODES)
            for mode in MODES[offset:] + MODES[:offset]:
                options = query_options(index_arn, mode, query, vector)
                hits, elapsed_ms = call_query(client, options)
                keys = [hit["key"] for hit in hits]
                rank = next((i for i, key in enumerate(keys, 1) if key in query.expected_keys), None)
                rows.append({
                    "group": query.group,
                    "query": query.text,
                    "expected_keys": query.expected_keys,
                    "mode": mode,
                    "repeat": repeat + 1,
                    "rank": rank,
                    "elapsed_ms": elapsed_ms,
                    "hits": hits,
                })
    return rows


def check_filter(client, index_arn, corpus, queries, query_vectors, rows):
    categories = {doc.key: doc.category for doc in corpus}
    query_inputs = {
        query.text: (query, vector)
        for query, vector in zip(queries, query_vectors, strict=True)
    }
    for row in rows:
        if row["mode"] != "ハイブリッド":
            continue
        query, vector = query_inputs[row["query"]]
        category = categories[query.expected_keys[0]]
        unfiltered = [hit["key"] for hit in row["hits"]]
        if not any(categories[key] != category for key in unfiltered):
            continue
        if not any(key in query.expected_keys for key in unfiltered):
            continue

        options = query_options(index_arn, "ハイブリッド", query, vector, category=category)
        hits, _ = call_query(client, options)
        keys = [hit["key"] for hit in hits]
        if not keys or any(categories.get(key) != category for key in keys):
            raise RuntimeError(f"Metadata filter returned invalid hits for category {category}")
        return {
            "status": "passed",
            "query": query.text,
            "category": category,
            "baseline_repeat": row["repeat"],
            "unfiltered_keys": unfiltered,
            "keys": keys,
        }
    return {"status": "inconclusive"}


def render_report(result):
    rows = result["rows"]
    first_pass = [row for row in rows if row["repeat"] == 1]
    filter_check = result["filter"]
    search_count = len(rows) + int(filter_check["status"] != "inconclusive")
    lines = [
        "### 東京リージョンの実測",
        "",
        f"{result['date']}、東京リージョン、FAQ100件、検索語15件、各方式{result['repeats']}周。",
        f"検索APIは合計{search_count}回。",
        "Hit@5は初回の各検索語について、正解文書が上位5件に1件でも入れば1件と数えた。",
        "応答時間はローカルからSDK呼び出し完了まで。埋め込み時間を除く。",
        "",
        "| 方式 | 全体 Hit@5 | 型番 | 言い換え | 混合 | 方式別の最初の1回 | 2周目以降の中央値 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode in MODES:
        mode_rows = [row for row in rows if row["mode"] == mode]
        first_mode_rows = [row for row in mode_rows if row["repeat"] == 1]
        hits_by_group = []
        for group in (None, "型番", "言い換え", "混合"):
            group_rows = [row for row in first_mode_rows if group is None or row["group"] == group]
            hit_count = sum(row["rank"] is not None for row in group_rows)
            hits_by_group.append(f"{hit_count}/{len(group_rows)}")
        repeat_times = [row["elapsed_ms"] for row in mode_rows if row["repeat"] > 1]
        median_text = f"{median(repeat_times):.1f} ms" if repeat_times else "計測なし"
        lines.append(f"| {mode} | {' | '.join(hits_by_group)} | "
                     f"{mode_rows[0]['elapsed_ms']:.1f} ms | {median_text} |")
    lines += [
        "",
        "| 検索語 | 全文の正解順位 | ベクトルの正解順位 | ハイブリッドの正解順位 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for query in dict.fromkeys(row["query"] for row in first_pass):
        ranks = {row["mode"]: row["rank"] for row in first_pass if row["query"] == query}
        cells = " | ".join(str(ranks[mode]) if ranks[mode] else "圏外" for mode in MODES)
        lines.append(f"| {query} | {cells} |")
    lines.append("")
    if filter_check["status"] == "passed":
        lines.append(
            f"{filter_check['baseline_repeat']}周目の「{filter_check['query']}」を使ったカテゴリ絞り込みで "
            f"`{filter_check['category']}` の文書だけが{len(filter_check['keys'])}件返った。"
        )
    elif filter_check["status"] == "failed":
        lines.append(f"カテゴリ絞り込みの確認に失敗した。{filter_check['error']}")
    else:
        lines.append("カテゴリ絞り込みは判定不能。絞り込みで除外を確認できる検索語がなかった。")
    return "\n".join(lines) + "\n"


def resource_exists(lookup):
    try:
        lookup()
    except ClientError as error:
        if error.response["Error"]["Code"] == "NotFoundException":
            return False
        raise
    return True


def uncertain_aws_response(error):
    if not isinstance(error, ClientError):
        return True
    code = error.response["Error"]["Code"]
    status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return code in AMBIGUOUS_CREATE_ERRORS or status in AMBIGUOUS_HTTP_STATUSES


def cleanup_resource(arn, delete, preceding_error=None):
    try:
        delete()
    except (*AWS_REQUEST_ERRORS, RuntimeError) as cleanup_error:
        message = f"Cleanup failed for {arn}: {cleanup_error}"
        if preceding_error is not None:
            message = f"{preceding_error}\n{message}"
        raise RuntimeError(message) from cleanup_error


@contextmanager
def created_resource(arn, create, lookup, delete):
    try:
        create()
    except AWS_REQUEST_ERRORS as error:
        if not uncertain_aws_response(error):
            raise
        for delay in CREATE_LOOKUP_DELAYS:
            if delay:
                sleep(delay)
            try:
                found = resource_exists(lookup)
            except AWS_REQUEST_ERRORS as lookup_error:
                if uncertain_aws_response(lookup_error):
                    continue
                if lookup_error.response["Error"]["Code"] in {"TooManyRequestsException", "429"}:
                    continue
                raise RuntimeError(f"Could not verify the create outcome for {arn}: {lookup_error}") from lookup_error
            if found:
                cleanup_resource(arn, delete, error)
                break
        else:
            raise RuntimeError(f"Create outcome unresolved for {arn}. Check for leftover resources.") from error
        raise
    try:
        yield
    except BaseException as error:
        cleanup_resource(arn, delete, error)
        raise
    else:
        cleanup_resource(arn, delete)


@contextmanager
def temporary_index(client, account):
    bucket_name = f"learning-s3v-{uuid4().hex}"
    bucket_arn = f"arn:aws:s3vectors:{REGION}:{account}:bucket/{bucket_name}"
    index_arn = f"{bucket_arn}/index/{INDEX_NAME}"
    lookup_bucket = partial(client.get_vector_bucket, vectorBucketArn=bucket_arn)

    def delete_bucket():
        client.delete_vector_bucket(vectorBucketArn=bucket_arn)
        if resource_exists(lookup_bucket):
            raise RuntimeError(f"Vector bucket still exists: {bucket_arn}")
        print(f"Confirmed deleted: {bucket_name}", flush=True)

    print(f"Vector bucket for this run: {bucket_name}", flush=True)
    with created_resource(
        bucket_arn,
        partial(client.create_vector_bucket, vectorBucketName=bucket_name),
        lookup_bucket,
        delete_bucket,
    ):
        with created_resource(
            index_arn,
            partial(client.create_index, **index_options(bucket_arn)),
            partial(client.get_index, indexArn=index_arn),
            partial(client.delete_index, indexArn=index_arn),
        ):
            yield index_arn


def aws_session(profile, expected_account):
    config = Config(
        retries={"total_max_attempts": 1},
        connect_timeout=5,
        read_timeout=15,
        ignore_configured_endpoint_urls=True,
    )
    session = boto3.Session(profile_name=profile, region_name=REGION)
    account = session.client("sts", config=config).get_caller_identity()["Account"]
    if account != expected_account:
        raise ValueError("STS account differs from --expected-account. No resources were created.")
    return session.client("s3vectors", config=config)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Create and delete a temporary AWS index")
    parser.add_argument("--profile", help="AWS profile for a live run")
    parser.add_argument("--expected-account", help="Approved 12-digit AWS account for a live run")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    calls = args.repeats * len(QUERIES) * len(MODES) + 1
    if args.repeats < 1 or calls > MAX_QUERIES:
        parser.error(f"repeats must allow 1–{MAX_QUERIES} total QueryVectors calls")
    if args.live and (not args.profile or not re.fullmatch(r"[0-9]{12}", args.expected_account or "")):
        parser.error("--live requires --profile and --expected-account (12 digits)")
    return args, calls


def main():
    args, calls = parse_args()
    corpus = documents()
    validate_fixtures(corpus, QUERIES)
    passage_vectors, query_vectors = embed(corpus, QUERIES)
    batch, logical_bytes = prepare_batch(corpus, passage_vectors)
    print(f"{len(batch)} FAQ, {len(QUERIES)} queries, {DIMENSION} dimensions, "
          f"{logical_bytes} estimated logical bytes, {calls} planned AWS searches")
    if not args.live:
        return

    client = aws_session(args.profile, args.expected_account)
    RESULTS.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    output_stem = RESULTS / f"{now:%Y%m%dT%H%M%S%fZ}-{uuid4().hex}"
    with temporary_index(client, args.expected_account) as index_arn:
        client.put_vectors(indexArn=index_arn, vectors=batch)
        rows = measure(client, index_arn, QUERIES, query_vectors, args.repeats)
        filter_error = None
        try:
            filter_check = check_filter(client, index_arn, corpus, QUERIES, query_vectors, rows)
        except (*AWS_REQUEST_ERRORS, RuntimeError) as error:
            filter_error = error
            filter_check = {"status": "failed", "error": str(error)}
        result = {
            "date": now.astimezone(JST).date().isoformat(),
            "region": REGION,
            "model": f"{MODEL}@{MODEL_REVISION}",
            "repeats": args.repeats,
            "rows": rows,
            "filter": filter_check,
        }
        output_stem.with_suffix(".json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        output_stem.with_suffix(".md").write_text(render_report(result), encoding="utf-8")
        print(f"Results saved to {output_stem}.json and {output_stem}.md", flush=True)
        if filter_error is not None:
            raise filter_error
        if filter_check["status"] == "inconclusive":
            print("カテゴリ絞り込みは判定不能。計測結果を保存しました。", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except (*AWS_REQUEST_ERRORS, ValueError, RuntimeError) as error:
        sys.exit(str(error))
