import json
import unittest
from contextlib import nullcontext
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, call, patch
from urllib.parse import urlsplit
from uuid import UUID

import boto3
from botocore.awsrequest import AWSResponse
from botocore.config import Config
from botocore.exceptions import ClientError, ReadTimeoutError, SSLError
from botocore.stub import Stubber

from experiment import (
    DIMENSION,
    INDEX_NAME,
    MODES,
    REGION,
    aws_session,
    check_filter,
    index_options,
    main,
    measure,
    render_report,
    temporary_index,
    validate_fixtures,
)
from fixtures import QUERIES, Document, Query, documents

ACCOUNT = "123456789012"
BUCKET_ID = UUID(int=1)
BUCKET_NAME = f"learning-s3v-{BUCKET_ID.hex}"
BUCKET_ARN = f"arn:aws:s3vectors:{REGION}:{ACCOUNT}:bucket/{BUCKET_NAME}"
INDEX_ARN = f"{BUCKET_ARN}/index/{INDEX_NAME}"
VECTOR = [1.0] + [0.0] * (DIMENSION - 1)


def stub_client():
    return boto3.client(
        "s3vectors",
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        config=Config(retries={"total_max_attempts": 1}),
    )


class ExperimentTests(unittest.TestCase):
    def test_fixtures_have_judgments_for_all_queries(self):
        validate_fixtures(documents(), QUERIES)

    def test_requests_and_report_use_the_three_rankings(self):
        queries = [
            Query("型番", "型番検索", ("right",)),
            Query("言い換え", "言い換え検索", ("right",)),
            Query("混合", "混合検索", ("right",)),
        ]
        client = stub_client()
        with Stubber(client) as stub:
            for repeat in range(2):
                for number, query in enumerate(queries):
                    offset = (repeat + number) % 3
                    text = {"queryTexts": [{"text": query.text, "metadataKey": "body"}],
                            "returnScores": True}
                    vector = {"queryVector": {"float32": VECTOR}}
                    options = {
                        "全文": text,
                        "ベクトル": {**vector, "returnDistance": True},
                        "ハイブリッド": {**text, **vector},
                    }
                    hits = {
                        "全文": [],
                        "ベクトル": [{"key": "distractor"}, {"key": "right"}],
                        "ハイブリッド": [{"key": "right"}],
                    }
                    for mode in MODES[offset:] + MODES[:offset]:
                        stub.add_response(
                            "query_vectors",
                            {"vectors": hits[mode], "distanceMetric": "cosine"},
                            {"indexArn": INDEX_ARN, "topK": 5, **options[mode]},
                        )
            rows = measure(client, INDEX_ARN, queries, [VECTOR] * len(queries), repeats=2)
            stub.assert_no_pending_responses()

        report = render_report({
            "date": "2026-11-20",
            "repeats": 2,
            "rows": rows,
            "filter": {
                "status": "passed", "query": "混合検索", "category": "test",
                "baseline_repeat": 1, "keys": ["right"],
            },
        })
        self.assertIn("| 全文 | 0/3 | 0/1 | 0/1 | 0/1 |", report)
        self.assertIn("| ベクトル | 3/3 | 1/1 | 1/1 | 1/1 |", report)
        self.assertIn("| ハイブリッド | 3/3 | 1/1 | 1/1 | 1/1 |", report)
        self.assertIn("| 混合検索 | 圏外 | 2 | 1 |", report)

    def test_deletes_temporary_resources_when_measurement_fails(self):
        client = stub_client()
        with Stubber(client) as stub, patch("experiment.uuid4", return_value=BUCKET_ID):
            stub.add_response("create_vector_bucket", {"vectorBucketArn": BUCKET_ARN},
                              {"vectorBucketName": BUCKET_NAME})
            stub.add_response("create_index", {"indexArn": INDEX_ARN}, index_options(BUCKET_ARN))
            stub.add_response("delete_index", {}, {"indexArn": INDEX_ARN})
            stub.add_response("delete_vector_bucket", {}, {"vectorBucketArn": BUCKET_ARN})
            stub.add_client_error("get_vector_bucket", "NotFoundException", http_status_code=404,
                                  expected_params={"vectorBucketArn": BUCKET_ARN})
            with self.assertRaisesRegex(RuntimeError, "measurement failed"):
                with temporary_index(client, ACCOUNT) as arn:
                    self.assertEqual(arn, INDEX_ARN)
                    raise RuntimeError("measurement failed")
            stub.assert_no_pending_responses()

    def test_account_mismatch_stops_before_s3_client_is_created(self):
        sts = Mock()
        sts.get_caller_identity.return_value = {"Account": "999999999999"}
        with patch("experiment.boto3.Session") as session:
            session.return_value.client.return_value = sts
            with self.assertRaisesRegex(ValueError, "STS account differs"):
                aws_session("test", ACCOUNT)
            session.return_value.client.assert_called_once()
            self.assertEqual(session.return_value.client.call_args.args, ("sts",))

    def test_sts_and_vectors_use_the_same_frozen_credentials(self):
        source = Mock()
        credentials = source.get_credentials.return_value
        credentials.get_frozen_credentials.return_value = SimpleNamespace(
            access_key="test-key", secret_key="test-secret", token="test-token"
        )
        verified = Mock()
        sts = Mock()
        sts.get_caller_identity.return_value = {"Account": ACCOUNT}
        vectors = Mock()
        verified.client.side_effect = [sts, vectors]
        with patch("experiment.boto3.Session", side_effect=[source, verified]) as session:
            self.assertIs(aws_session("test", ACCOUNT), vectors)

        credentials.get_frozen_credentials.assert_called_once()
        self.assertEqual(session.call_args_list, [
            call(profile_name="test", region_name=REGION),
            call(
                profile_name="test", region_name=REGION, aws_access_key_id="test-key",
                aws_secret_access_key="test-secret", aws_session_token="test-token",
            ),
        ])
        self.assertEqual([entry.args[0] for entry in verified.client.call_args_list], ["sts", "s3vectors"])

    def test_cleans_up_bucket_after_create_response_times_out(self):
        client = Mock()
        client.create_vector_bucket.side_effect = ReadTimeoutError(endpoint_url="https://test")
        missing = ClientError({"Error": {"Code": "NotFoundException"}}, "GetVectorBucket")
        client.get_vector_bucket.side_effect = [{"vectorBucket": {}}, missing]

        with patch("experiment.uuid4", return_value=BUCKET_ID):
            with self.assertRaises(ReadTimeoutError):
                with temporary_index(client, ACCOUNT):
                    self.fail("measurement started after a timeout")

        self.assertEqual(client.mock_calls, [
            call.create_vector_bucket(vectorBucketName=BUCKET_NAME),
            call.get_vector_bucket(vectorBucketArn=BUCKET_ARN),
            call.delete_vector_bucket(vectorBucketArn=BUCKET_ARN),
            call.get_vector_bucket(vectorBucketArn=BUCKET_ARN),
        ])

    def test_cleans_up_index_after_create_response_times_out(self):
        client = Mock()
        timeout = ClientError({"Error": {"Code": "RequestTimeoutException"}}, "CreateIndex")
        client.create_index.side_effect = timeout
        client.get_vector_bucket.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException"}}, "GetVectorBucket"
        )

        with patch("experiment.uuid4", return_value=BUCKET_ID):
            with self.assertRaisesRegex(ClientError, "RequestTimeoutException"):
                with temporary_index(client, ACCOUNT):
                    self.fail("measurement started after a timeout")

        self.assertEqual(client.mock_calls, [
            call.create_vector_bucket(vectorBucketName=BUCKET_NAME),
            call.create_index(**index_options(BUCKET_ARN)),
            call.get_index(indexArn=INDEX_ARN),
            call.delete_index(indexArn=INDEX_ARN),
            call.delete_vector_bucket(vectorBucketArn=BUCKET_ARN),
            call.get_vector_bucket(vectorBucketArn=BUCKET_ARN),
        ])

    def test_create_conflict_does_not_delete_a_preexisting_bucket(self):
        client = Mock()
        client.create_vector_bucket.side_effect = ClientError(
            {"Error": {"Code": "ConflictException"}}, "CreateVectorBucket"
        )
        with patch("experiment.uuid4", return_value=BUCKET_ID):
            with self.assertRaisesRegex(ClientError, "ConflictException"):
                with temporary_index(client, ACCOUNT):
                    self.fail("measurement started after a conflict")
        self.assertEqual(client.mock_calls, [call.create_vector_bucket(vectorBucketName=BUCKET_NAME)])

    def test_rechecks_after_gateway_timeout_until_bucket_appears(self):
        client = Mock()
        client.create_vector_bucket.side_effect = ClientError(
            {"Error": {"Code": "504"}, "ResponseMetadata": {"HTTPStatusCode": 504}},
            "CreateVectorBucket",
        )
        missing = ClientError({"Error": {"Code": "NotFoundException"}}, "GetVectorBucket")
        unavailable = ClientError(
            {"Error": {"Code": "ServiceUnavailableException"}}, "GetVectorBucket"
        )
        client.get_vector_bucket.side_effect = [unavailable, missing, {"vectorBucket": {}}, missing]

        with patch("experiment.uuid4", return_value=BUCKET_ID), patch("experiment.sleep"):
            with self.assertRaisesRegex(ClientError, "504"):
                with temporary_index(client, ACCOUNT):
                    self.fail("measurement started after a gateway timeout")

        self.assertEqual(client.get_vector_bucket.call_count, 4)
        client.delete_vector_bucket.assert_called_once_with(vectorBucketArn=BUCKET_ARN)

    def test_keeps_unresolved_index_arn_when_bucket_cleanup_fails(self):
        client = Mock()
        client.create_index.side_effect = ReadTimeoutError(endpoint_url="https://test")
        client.get_index.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException"}}, "GetIndex"
        )
        client.delete_vector_bucket.side_effect = ClientError(
            {"Error": {"Code": "ConflictException"}}, "DeleteVectorBucket"
        )

        with patch("experiment.uuid4", return_value=BUCKET_ID), patch("experiment.sleep"):
            with self.assertRaises(RuntimeError) as failure:
                with temporary_index(client, ACCOUNT):
                    self.fail("measurement started despite an unresolved index")

        self.assertIn(INDEX_ARN, str(failure.exception))
        self.assertIn("ConflictException", str(failure.exception))
        self.assertEqual(client.get_index.call_count, 3)

    def test_reconciles_bucket_after_create_tls_error(self):
        client = Mock()
        client.create_vector_bucket.side_effect = SSLError(endpoint_url="https://test", error="TLS failed")
        client.get_vector_bucket.side_effect = [
            {"vectorBucket": {}},
            ClientError({"Error": {"Code": "NotFoundException"}}, "GetVectorBucket"),
        ]
        with patch("experiment.uuid4", return_value=BUCKET_ID):
            with self.assertRaises(SSLError):
                with temporary_index(client, ACCOUNT):
                    self.fail("measurement started after a TLS error")
        client.delete_vector_bucket.assert_called_once_with(vectorBucketArn=BUCKET_ARN)

    def test_reconciles_bucket_after_ambiguous_sdk_response(self):
        for status, body, exception in (
            (504, b"\xff", UnicodeDecodeError),
            (504, b"[]", AttributeError),
            (524, b'{"message":"gateway timeout"}', ClientError),
        ):
            with self.subTest(status=status, body=body):
                client = stub_client()
                responses = []
                for status, body, headers in (
                    (status, body, {}),
                    (200, b'{"vectorBucket":{}}', {}),
                    (200, b"{}", {}),
                    (404, b'{"message":"missing"}', {"x-amzn-errortype": "NotFoundException"}),
                ):
                    raw = Mock()
                    raw.stream.return_value = [body]
                    responses.append(AWSResponse("https://test", status, headers, raw))

                with (
                    patch("experiment.uuid4", return_value=BUCKET_ID),
                    patch.object(client._endpoint.http_session, "send", side_effect=responses) as send,
                    self.assertRaises(exception),
                ):
                    with temporary_index(client, ACCOUNT):
                        self.fail("measurement started after an invalid response")

                self.assertEqual(
                    [urlsplit(sent.args[0].url).path for sent in send.call_args_list],
                    ["/CreateVectorBucket", "/GetVectorBucket", "/DeleteVectorBucket", "/GetVectorBucket"],
                )

    def test_reports_unresolved_arn_after_three_lookups(self):
        client = Mock()
        client.create_vector_bucket.side_effect = ReadTimeoutError(endpoint_url="https://test")
        client.get_vector_bucket.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException"}}, "GetVectorBucket"
        )

        with patch("experiment.uuid4", return_value=BUCKET_ID), patch("experiment.sleep"):
            with self.assertRaisesRegex(RuntimeError, BUCKET_ARN):
                with temporary_index(client, ACCOUNT):
                    self.fail("measurement started despite an unresolved create")

        self.assertEqual(client.get_vector_bucket.call_count, 3)
        client.delete_vector_bucket.assert_not_called()

    def test_filter_requires_proof_that_another_category_was_excluded(self):
        corpus = [Document("right", "coffee", "豆挽き"), Document("other", "air", "送風")]
        queries = [Query("型番", "型番", ("right",)), Query("言い換え", "症状", ("right",))]
        rows = [
            {"mode": "ハイブリッド", "repeat": 1, "query": "型番", "hits": [{"key": "right"}]},
            {"mode": "ハイブリッド", "repeat": 1, "query": "症状", "hits": [{"key": "right"}]},
            {"mode": "ハイブリッド", "repeat": 2, "query": "症状",
             "hits": [{"key": "right"}, {"key": "other"}]},
        ]
        expected_request = {
            "indexArn": INDEX_ARN,
            "topK": 5,
            "queryTexts": [{"metadataKey": "body", "text": "症状"}],
            "queryVector": {"float32": VECTOR},
            "returnScores": True,
            "filter": {"category": {"$eq": "coffee"}},
        }
        for keys in (["right"], ["right", "other"]):
            with self.subTest(keys=keys), Stubber(stub_client()) as stub:
                stub.add_response(
                    "query_vectors", {"vectors": [{"key": key} for key in keys], "distanceMetric": "cosine"},
                    expected_request,
                )
                if "other" in keys:
                    with self.assertRaisesRegex(RuntimeError, "Metadata filter returned invalid hits"):
                        check_filter(stub.client, INDEX_ARN, corpus, queries, [VECTOR] * 2, rows)
                else:
                    result = check_filter(stub.client, INDEX_ARN, corpus, queries, [VECTOR] * 2, rows)
                    self.assertEqual(result["unfiltered_keys"], ["right", "other"])
                    self.assertEqual(result["baseline_repeat"], 2)
                    self.assertEqual(result["keys"], ["right"])
                stub.assert_no_pending_responses()

    def test_keeps_rankings_when_filter_cannot_be_verified(self):
        client = Mock()
        client.query_vectors.return_value = {"vectors": []}
        args = SimpleNamespace(live=True, profile="test", expected_account=ACCOUNT, repeats=1)
        with TemporaryDirectory() as directory:
            results = Path(directory)
            with (
                patch("experiment.RESULTS", results),
                patch("experiment.parse_args", return_value=(args, 46)),
                patch("experiment.embed", return_value=([VECTOR] * 100, [VECTOR] * 15)),
                patch("experiment.aws_session", return_value=client),
                patch("experiment.temporary_index", return_value=nullcontext(INDEX_ARN)),
                patch("sys.stderr", new_callable=StringIO) as stderr,
            ):
                main()
            result = json.loads(next(results.glob("*.json")).read_text(encoding="utf-8"))
            report = next(results.glob("*.md")).read_text(encoding="utf-8")

        self.assertEqual(client.query_vectors.call_count, 45)
        self.assertEqual(len(result["rows"]), 45)
        self.assertEqual(result["filter"]["status"], "inconclusive")
        self.assertIn("合計45回", report)
        self.assertIn("カテゴリ絞り込みは判定不能", report)
        self.assertIn("カテゴリ絞り込みは判定不能", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
