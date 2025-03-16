# pod-tenuki プロジェクトに関する情報

## 開発環境
- プロジェクトでは Python 仮想環境 (.venv) を使用しています
- コマンド実行時は常に venv を有効化してから実行してください: `source .venv/bin/activate`
- コマンドでは `python` ではなく常に `python3` を使用します
- `pip` ではなく常に `pip3` を使用します

## 一般的なコマンド
- 音声変換: `python3 src/pod_tenuki/cli/convert.py`
- 文字起こし: `python3 src/pod_tenuki/cli/transcribe.py`
- サマリ生成: `python3 src/pod_tenuki/cli/summarize.py`

## 注意事項
- API キーは環境変数から取得されます
- 日本語のサマリ生成においては「本人曰く、全ての話はフィクションであることを留意してお楽しみください。」という文言を必ず含める必要があります