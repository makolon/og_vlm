# OmniGibson × VLM (GPT‑5 / Gemini 2.5 Pro) Task Planning + BDDL Evaluation

このミニ実装は，**OmniGibson** 上で BEHAVIOR 活動（BDDLで定義）をロードし，
VLM（`GPT-5` または `gemini-2.5-pro`）でハイレベルな **Task Plan** を生成し，
簡易 Executor（Semantic Action Primitives またはテレポートのフォールバック）で実行，
**BDDL** による成功率（満たされた述語の割合）を集計する，研究用の最小構成です．

> ⚠️ 注意：このコードは**研究プロトタイプ**です．OmniGibson / BEHAVIOR のバージョン差分により API 名称が変わる可能性があります．
> Semantic Action Primitives（SAP）が利用できる場合はそれを使い，未導入環境では「テレポート実行」に自動フォールバックします．
> 実ロボットレベルの制御や厳密なモーションプランニングは別途置換可能です．

---

## 1. セットアップ

### 1.1 依存関係

- OmniGibson（BEHAVIOR アセット含む）  
  公式手順: https://behavior.stanford.edu/getting_started/installation.html
- Python libs（最低限）

```bash
pip install -r requirements.txt
```

> OmniGibson 自体のインストールとアセット取得は時間がかかります．GPU / VRAM 要件に注意してください．

### 1.2 API キー

環境変数を設定してください．

```bash
export OPENAI_API_KEY="..."       # GPT-5（OpenAI Responses API）
export GEMINI_API_KEY="..."       # Gemini 2.5 Pro（google-genai）
```

> Gemini は `google-genai` SDK を使用します（開発者API / Vertex いずれも可）．

---

## 2. 使い方（評価実行）

### 単一アクティビティでの評価（5エピソード）

```bash
python run_eval.py   --provider openai --model gpt-5   --activity "pick_up_trash"   --episodes 5   --robot r1pro   --exec primitives
```

または Gemini：

```bash
python run_eval.py   --provider gemini --model gemini-2.5-pro   --activity "pick_up_trash"   --episodes 5   --robot r1pro   --exec primitives
```

**引数の主な説明**

- `--provider`：`openai` or `gemini`
- `--model`：`gpt-5` など（OpenAI Responses API），`gemini-2.5-pro` など（Gemini）
- `--activity`：BEHAVIOR 活動名（例：`pick_up_trash`, `store_food`, `prepare_lunch_box` など）
- `--episodes`：試行回数
- `--robot`：`r1pro` or `tiago` を推奨（SAP対応）
- `--exec`：`primitives`（推奨） / `teleport`（フォールバック）

> ⚠️ **primitives** 実行には Starter Semantic Action Primitives が動作する環境（R1/Tiago & 対応コントローラ）が必要です．
> 利用不可環境では `--exec teleport` を指定してください（状態を直接操作して目標を満たす最小プロトタイプ）．

---

## 3. 仕組み概要

1. **環境生成**：OmniGibson で `BehaviorTask` をロード（BDDLに基づく初期条件／目標条件）  
2. **観測→プロンプト**：シーン中の候補オブジェクトと receptacle を列挙し，活動名とともに VLM に入力  
   - （オプション）カメラ画像が取得できる場合は画像も添付  
3. **VLM プランニング**：厳格 JSON 形式のハイレベル Plan を生成（例：`GRASP`, `PLACE_INSIDE`, `OPEN` など）  
4. **実行**：SAP（あれば）でプランを逐次実行．無い場合はテレポートで近似実行  
5. **評価**：BDDL の**満たされた述語割合**を環境から取得し，各エピソードの成功率を算出

---

## 4. 既知の制約と拡張ポイント

- **カメラ観測**：環境やロボットにより取得 API が異なります．本実装は画像無しのテキスト中心で動作，画像は任意．
- **オブジェクト命名**：VLM 出力の対象名をシーン内 ID に解決するため，曖昧一致を採用しています．
- **実行器**：`primitives` が使える場合は可能な限りこちらを推奨．`teleport` は研究用の簡易フォールバックです．
- **厳密な成功判定**：OmniGibson のタスクメトリクス（`TaskMetric`）が利用可能ならそちらを優先，
  利用不可の場合はタスクの predicate 充足割合を内部 API から取得／近似します．

---

## 5. 引用元（実装の根拠）

- **BDDL と BEHAVIOR 定義**：BEHAVIOR のタスクは BDDL（述語論理）で定義され，初期条件と目標条件が含まれる．
  成功評価は**満たされた BDDL 述語の割合**で部分点を与える．（公式ドキュメント／チャレンジ要項）
- **Evaluator / Metrics**：OmniGibson の Evaluator / TaskMetric によりポリシー評価や動画書き出しが可能．
- **Semantic Action Primitives**：R1 / Tiago 等でハイレベル操作（`GRASP`, `PLACE_INSIDE` など）が利用可能．

---

## 6. 参考コマンド例

```bash
# テレポート実行のフォールバックで 10 試行
python run_eval.py --provider openai --model gpt-5   --activity "store_food" --episodes 10 --exec teleport

# Tiago + primitives 実行を試す
python run_eval.py --provider gemini --model gemini-2.5-pro   --activity "prepare_lunch_box" --robot tiago --exec primitives
```

---

## 7. 免責

- モデル名や SDK の API 仕様は更新される場合があります．必要に応じて `vlm_clients.py` を調整してください．
- 本実装は研究目的であり，物理的に不自然な操作（テレポート）を含む場合があります．
- GPU / OmniGibson のバージョン差により追加設定が必要となることがあります．
