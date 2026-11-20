"""Deterministic Japanese product FAQs and judgments for the search comparison."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    key: str
    category: str
    body: str


@dataclass(frozen=True)
class Query:
    group: str
    text: str
    expected_keys: tuple[str, ...]


PRODUCTS = (
    ("ARX900", "空気清浄機", "air"),
    ("ARX910", "空気清浄機", "air"),
    ("HML200", "加湿器", "humidifier"),
    ("HML210", "加湿器", "humidifier"),
    ("SVR300", "ロボット掃除機", "cleaner"),
    ("SVR310", "ロボット掃除機", "cleaner"),
    ("LNX400", "照明コントローラー", "lighting"),
    ("LNX410", "照明コントローラー", "lighting"),
    ("BRW500", "コーヒーメーカー", "coffee"),
    ("BRW510", "コーヒーメーカー", "coffee"),
)

TOPICS = {
    "power": "電源が入らないときは、コンセントを抜いて30秒待ってから差し直してください。",
    "setup": "初期設定をやり直すには、設定ボタンを長押しして出荷時の状態に戻します。",
    "network": "無線LANへの接続に失敗するときは、2.4GHzのSSIDを選び直してください。",
    "sound": "動作中に異音がするときは、本体を停止し、ぐらつきのない水平な場所に置いてください。",
    "light": "状態ランプが橙色のままの場合は、保守モードを解除すると通常表示に戻ります。",
    "sensor": "センサーが反応しにくい場合は、検知窓の汚れを乾いた布で拭き取ります。",
    "update": "更新が途中で停止したら、通信が安定してからアプリで更新を再開してください。",
    "timer": "予約した時刻に作動しない場合は、本体の時計と曜日設定を確認してください。",
    "care": "日常のお手入れでは、本体を停止して水気を切り、付属のブラシで汚れを落とします。",
    "service": "修理の受付には保証書と購入日が必要です。故障時は販売店へ相談してください。",
}

PRODUCT_NOTES = {
    ("ARX910", "care"): "フィルターに積もったほこりは、掃除機の弱い吸引で除去してください。",
    ("HML200", "sensor"): "水位検知部に白い析出物が付くと、満水でも給水警告を示します。",
    ("SVR310", "power"): "充電台に戻っても充電しない場合は、本体と充電台の金属端子を拭きます。",
    ("LNX400", "light"): "停電復旧後に照明が点滅を繰り返すときは、壁スイッチを切って1分待ちます。",
    ("BRW510", "sound"): "豆挽きの最中の甲高い音は、ホッパーに混入した硬い異物が原因のことがあります。",
}


def documents() -> list[Document]:
    corpus = []
    for model, name, category in PRODUCTS:
        for topic, answer in TOPICS.items():
            note = PRODUCT_NOTES.get((model, topic), "")
            body = f"{model} {name} よくある質問。{answer}{note}"
            corpus.append(Document(f"{model}-{topic}", category, body))
    return corpus


QUERIES = (
    *(
        Query("型番", model, tuple(f"{model}-{topic}" for topic in TOPICS))
        for model in ("ARX900", "HML210", "SVR300", "LNX410", "BRW500")
    ),
    Query("言い換え", "集じん用の網がごみで詰まった", ("ARX910-care",)),
    Query("言い換え", "タンクに十分入れたのに水を足すよう表示される", ("HML200-sensor",)),
    Query("言い換え", "お掃除機がドックに着いても電池が回復しない", ("SVR310-power",)),
    Query("言い換え", "電気が復旧したあと部屋の明かりがチカチカする", ("LNX400-light",)),
    Query("言い換え", "ミルを回すとキーッと鳴る", ("BRW510-sound",)),
    Query("混合", "ARX900 Wi-Fiにつながらない", ("ARX900-network",)),
    Query("混合", "HML210 指定時間になっても動かない", ("HML210-timer",)),
    Query("混合", "SVR310 ドックに戻っても電池が増えない", ("SVR310-power",)),
    Query("混合", "LNX400 電気が戻ったら明かりがちらつく", ("LNX400-light",)),
    Query("混合", "BRW510 ミルがキーッと鳴る", ("BRW510-sound",)),
)
