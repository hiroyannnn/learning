import unittest
from unittest.mock import Mock, patch
from uuid import UUID

import boto3
from botocore.stub import Stubber

from experiment import (
    DIMENSION,
    INDEX_NAME,
    MODES,
    REGION,
    aws_session,
    index_options,
    measure,
    render_report,
    temporary_index,
    validate_fixtures,
)
from fixtures import QUERIES, Query, documents

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
            "filter": {"query": "混合検索", "category": "test", "keys": ["right"]},
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


if __name__ == "__main__":
    unittest.main()
