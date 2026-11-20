# S3 Vectors で日本語 FAQ を検索する

製品の型番と症状を一緒に検索するとき、S3 Vectors のハイブリッド検索で正解文書が見つかりやすくなるかを調べる。架空の製品10種に対するFAQ100件と、型番・言い換え・混合の検索語各5件を [fixtures.py](fixtures.py) に固定した。型番だけの場合は同じ製品のFAQ全件を正解とし、症状を含む場合は対応するFAQを1件指定した。

| 方式 | 同じ `QueryVectors` API に渡す値 | 順位付け |
| --- | --- | --- |
| 全文 | 検索語 | 日本語アナライザーとBM25 |
| ベクトル | 検索語の埋め込み | コサイン距離 |
| ハイブリッド | 検索語と埋め込み | 全文・ベクトルの順位をRRFで統合 |

本文を日本語で全文検索できるフィールドに設定し、カテゴリはメタデータの絞り込みに使う。3方式は同一のインデックスに対して実行する。埋め込みはローカルCPUで生成し、文書と検索語には E5 の `passage: ` と `query: ` を付ける。

[AWSのハイブリッド検索の仕様](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-hybrid-search.html) · [埋め込みモデル](https://huggingface.co/intfloat/multilingual-e5-small)

## ローカルで準備する

前提は Python 3.12 と `uv`。macOSで埋め込みを生成する場合、固定したPyTorchの配布対象は macOS 14以降のApple Silicon。

```sh
cd experiments/s3-vectors
uv run --locked --extra embedding experiment.py
```

初回は依存関係と固定リビジョンの公開モデルを取得する。100件の文書と15件の検索語の埋め込みを生成し、次元数、正解ID、投入サイズを検証する。ここまでAWS認証情報は不要。

## ローカルテスト

Docker 統合テストには Docker Engine 28.0.0 以降の、rootful でユーザー名前空間の再マッピングを使わないローカル環境が必要。 [Dockerのポート公開仕様](https://docs.docker.com/engine/network/port-publishing/)

```sh
uv run --locked python -m unittest -v test_experiment
bash run_emulator_test.sh
```

1行目は SDK のスタブで3方式のリクエスト、順位の集計、作成応答がタイムアウトした場合の削除、カテゴリ絞り込み、アカウント違いでの停止を確認する。2行目は Docker で AWS 公式 Emulator v1.0.533 を起動し、S3 Vectors の作成・投入・ベクトル順位・カテゴリ絞り込み・削除を同じSDKで確認する。テストは埋め込みの追加依存をインストールせず、AWS アカウントも不要。Docker ビルドはベースのダイジェストとRPMのSHA-256を固定する。SHA-256は、[AWS公式手順](https://docs.aws.amazon.com/emulator/latest/userguide/getting-started-linux.html) に従い配布元の署名を確認したRPMから取得した。テスト用コンテナへの接続はループバックに限定し、終了時にコンテナと一時認証情報を片付ける。既定ポートが使用中なら `S3V_EMULATOR_PORT=9298 bash run_emulator_test.sh` のように変更できる。

Emulator v1.0.533 の `QueryVectors` はベクトル距離で順位付けする。全文とハイブリッドのリクエスト・集計はスタブで検証し、日本語の全文検索・RRFの順位・応答時間は東京リージョンの実測を参照する。 [AWS Emulatorの利用手順](https://docs.aws.amazon.com/emulator/latest/userguide/getting-started-docker.html) · [固定版の検索実装](https://github.com/aws/aws-emulator/blob/v1.0.533/services/service-com-amazonaws-s3vectors-s3vectors/src/ops/query_vectors.rs)

2026年11月20日、Apple Silicon の macOS でSDKテスト12件と Docker 統合テスト1件が成功した。

## AWSで計測する

利用する個人アカウントと費用を確認・承認してから実行する。`AWS_PROFILE` と `AWS_ACCOUNT_ID` には、確認済みのプロファイルとアカウントIDを設定する。リージョンは `ap-northeast-1` 固定で、STS の照会結果が期待するアカウントIDと一致した場合に、その実行専用のベクトルバケットとインデックスを各1個作成する。

```sh
uv run --locked --extra embedding experiment.py --live --profile "$AWS_PROFILE" --expected-account "$AWS_ACCOUNT_ID"
```

`--repeats` は既定で3周。各周は15件×3方式。全周のハイブリッド検索結果から、正解と別カテゴリの文書を含む検索語を1件選び、絞り込み後に別カテゴリが除外されることを確認する。該当する検索語がなければ端末に判定不能と表示し、計測結果を保存する。既定は最大136検索、6周でも最大271検索。SDKの自動再試行は無効で、実行し直すと別の計測になる。必要な権限はバケットとインデックスの作成・削除、`GetVectorBucket`、`GetIndex`、`PutVectors`、`QueryVectors`、`GetVectors`。 [AWSの権限一覧](https://docs.aws.amazon.com/service-authorization/latest/reference/list_s3vectors.html)

2026年11月20日の東京リージョン公開単価では、上限300検索とその他API最大8回を見込んでも1回約0.0014 USD未満。投入上限は256 KiB。無料枠・クレジットは試算に含めず、削除後の継続費は0 USD。 [料金の計算方法](https://aws.amazon.com/s3/pricing/#S3_Vectors) · [東京の単価](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/20261120022349/ap-northeast-1/index.json)

計測結果は `results/` にJSONとMarkdownで出力する。1周目の検索語別の正解順位から Hit@5 を計算する。応答時間はクライアント側のAPI所要時間で、方式ごとの最初の1回と2周目以降の中央値を記録する。埋め込み生成時間は含めない。少量の合成データで検索結果の傾向を見るための測定であり、実運用の負荷や他サービスとの性能比較には追加計測が必要になる。

計測後は作成したインデックスとバケットを削除し、`Confirmed deleted` を表示する。作成応答がタイムアウトした場合は、その実行専用のARNで最大3回照合し、見つかったリソースを削除する。作成の結果を確定できなければ、確認が必要なARNをエラーに表示する。処理が中断した場合や削除を確認できない場合は、開始時に表示された `learning-s3v-...` の名前を使い、同じアカウントとリージョンで専用インデックス `faq` とバケットの残存を確認する。 [AWSの削除手順](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-buckets-delete.html)

## 結果

2026年11月20日、東京リージョンでFAQ100件と検索語15件を3周測定した。カテゴリ絞り込みの試行を含めて136検索。3周とも各方式のHit@5の件数は同じだった。専用インデックスとバケットを削除し、バケットを再取得して `NotFoundException` を確認した。公開単価による費用概算は約0.0008 USD。

| 方式 | 全体 Hit@5 | 型番 | 言い換え | 混合 | 全体 Hit@1 | 方式別の初回 | 2周目以降の中央値 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 全文 | 10/15 | 5/5 | 1/5 | 4/5 | 7/15 | 139.9 ms | 83.5 ms |
| ベクトル | 13/15 | 5/5 | 3/5 | 5/5 | 12/15 | 90.0 ms | 77.5 ms |
| ハイブリッド | 13/15 | 5/5 | 3/5 | 5/5 | 7/15 | 151.6 ms | 91.6 ms |

1周目の正解順位が変わった例。

| 検索語 | 全文 | ベクトル | ハイブリッド |
| --- | ---: | ---: | ---: |
| ARX900 Wi-Fiにつながらない | 3位 | 1位 | 2位 |
| BRW510 ミルがキーッと鳴る | 圏外 | 1位 | 4位 |
| タンクに十分入れたのに水を足すよう表示される | 圏外 | 1位 | 5位 |

型番だけの検索は、3方式とも5件すべてで1位が正解だった。型番と症状を組み合わせた検索では、ハイブリッドは全文のみで漏れた1件を拾い、ベクトルと同じ5/5だった。上の3例ではハイブリッドが全文より上に正解を返した一方、ベクトルでは正解がすべて1位だった。「混合クエリでハイブリッドが両方式を上回る」という仮説は外れた。このデータでは、Hit@1と応答時間の中央値でベクトル検索が最も良かった。

初回の実測で `coffee` の絞り込みを試した検索語は、絞り込み前後で同じ5件を返した。絞り込みによる除外は、カテゴリが異なる文書を用意したローカルテストで確認した。応答時間はローカルからSDKを呼び出して応答を受け取るまでで、ネットワーク時間を含む。対象が合成FAQ100件の1実験なので、実データでの精度や負荷時の応答時間は追加計測が必要。
