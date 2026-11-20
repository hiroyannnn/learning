# Amazon S3 Vectors で日本語 FAQ を検索する

日本語の架空FAQ100件を使い、同じ S3 Vectors インデックスで全文検索、ベクトル検索、ハイブリッド検索の順位と応答時間を比較します。
データと正解は [fixtures.py](fixtures.py) にあります。

## ローカルで試す

Python 3.12 と [uv](https://docs.astral.sh/uv/) を用意し、リポジトリのルートから実行します。
以下のテストに AWS アカウントや埋め込みモデルは不要です。

```sh
cd experiments/s3-vectors
uv run --locked python -m unittest -v test_experiment
```

SDKスタブで3方式のリクエスト、順位の集計、カテゴリ絞り込み、アカウント照合、リソース削除を確認します。
実際のAPI通信も試す場合は、同じディレクトリで AWS 公式 Emulator の統合テストを実行します。
Docker Engine 28以降のローカル環境（rootful、ユーザー名前空間の再マッピングなし）と、BuildKit、Bash、`curl` が必要です。
Docker のビルド対象は `amd64` または `arm64` です。初回のビルドではベースイメージと AWS の Emulator パッケージを取得します。

```sh
bash run_emulator_test.sh
```

このテストでは、作成、投入、ベクトル順位、カテゴリ絞り込み、削除を確認します。
Emulator v1.0.533 で確認できる順位付けはベクトル距離です。
日本語の全文検索、ハイブリッドの順位、応答時間は以下のAWS実測を参照してください。
ポートが競合する場合は `S3V_EMULATOR_PORT=9298 bash run_emulator_test.sh` で変更できます。
[AWS Emulatorの利用手順](https://docs.aws.amazon.com/emulator/latest/userguide/getting-started-docker.html) · [固定版の検索実装](https://github.com/aws/aws-emulator/blob/v1.0.533/services/service-com-amazonaws-s3vectors-s3vectors/src/ops/query_vectors.rs)

## 3方式の比較

2026年11月20日に東京リージョンで計測しました。FAQ100件、検索語15件を各方式3周、絞り込みの試行を含めて136検索です。
Hit@1とHit@5は、それぞれ初周の1位以内、5位以内に正解が入った検索語の数です。応答時間は2周目以降のSDK呼び出しの中央値で、ネットワーク時間を含みます。

| 方式 | `QueryVectors` の入力と順位付け | Hit@1 | Hit@5 | 応答時間 |
| --- | --- | ---: | ---: | ---: |
| 全文 | 検索語、日本語アナライザーとBM25 | 7/15 | 10/15 | 83.5 ms |
| ベクトル | 検索語の埋め込み、コサイン距離 | 12/15 | 13/15 | 77.5 ms |
| ハイブリッド | 検索語と埋め込み、RRFで順位を統合 | 7/15 | 13/15 | 91.6 ms |

型番だけの5件は、3方式とも正解が1位でした。
症状の言い換えだけの Hit@5 は、全文1/5、ベクトル3/5、ハイブリッド3/5でした。型番と症状の組み合わせでは、それぞれ4/5、5/5、5/5でした。
初回のAWS計測では絞り込み前後で同じ5件が返りました。別カテゴリが結果から外れることはローカルテストで確認しました。
現在のコードは、正解と別カテゴリの文書が両方含まれる検索結果を選んで絞り込みを試します。該当する結果がなければ、絞り込みは判定不能と表示し、3方式の結果を保存します。
[AWSの検索仕様](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-hybrid-search.html)

## AWSで再計測する

リポジトリのルートから `cd experiments/s3-vectors` で移動します。
まず `uv run --locked --extra embedding experiment.py` で、文書と検索語の384次元埋め込み、正解ID、投入サイズをローカルで検証できます。
初回は Python の依存関係と [multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) のモデルを取得します。
固定したPyTorchのwheelは、macOS 14以降のApple Silicon、glibc 2.28以降のLinux（x86-64、ARM64）、Windows x64向けです。コマンド例はBashで記載しています。

AWSで計測する場合は、利用する個人アカウント、東京リージョン（`ap-northeast-1`）の単価と費用を実行前に確認してください。
`AWS_PROFILE` と `AWS_ACCOUNT_ID` には使用するプロファイルと12桁のアカウントIDを設定します。
2026年11月20日の計測は公開単価で約0.0008 USDでした。 [S3 Vectorsの料金](https://aws.amazon.com/s3/pricing/#S3_Vectors) · [東京リージョンの当時の単価](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/20261120022349/ap-northeast-1/index.json)

プロファイルには `s3vectors:` の以下の権限が必要です。

- バケットとインデックスの管理 `CreateVectorBucket`、`GetVectorBucket`、`DeleteVectorBucket`、`CreateIndex`、`GetIndex`、`DeleteIndex`
- 投入と検索 `PutVectors`、`QueryVectors`、`GetVectors`

全文検索とメタデータ絞り込みには `QueryVectors` と `GetVectors` の両方が必要です。 [QueryVectorsの権限](https://docs.aws.amazon.com/cli/latest/reference/s3vectors/query-vectors.html#description)

```sh
uv run --locked --extra embedding experiment.py --live --profile "$AWS_PROFILE" --expected-account "$AWS_ACCOUNT_ID"
```

既定は3周で最大136検索です。 `--repeats` で変更できます（最大6周）。SDKの自動再試行は無効です。
STSでアカウントを照合してから、専用のバケットとインデックスを各1個作成します。

計測結果は `results/` にJSONとMarkdownで保存します。
終了時に専用のインデックスとバケットを削除し、確認できたら `Confirmed deleted` を表示します。
中断した場合や作成・削除結果が未確定の場合は、端末に出力されたバケット名またはARNを使い、同じアカウントとリージョンでバケットとインデックス `faq` の残存を確認します。
[AWSの削除手順](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-buckets-delete.html)
