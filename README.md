# Pod-Tenuki

Pod-Tenukiは、ポッドキャストの音声ファイルを処理するためのコマンドラインツールです。以下の機能を提供します：

1. **音声変換**: Auphonic APIを使用して音声ファイル（MP3、MP4、m4aなど）を指定のプリセットで変換
2. **文字起こし**: Google Gemini APIを使用して音声ファイルをテキストに変換
3. **要約**: OpenAI APIを使用して文字起こしからポッドキャストのタイトルと説明文を生成
4. **コスト追跡**: GeminiとOpenAI APIの使用コストを追跡して表示

## インストール

### 前提条件

- Python 3.8以上
- Auphonic APIキー
- Gemini APIキー
- OpenAI APIキー
- ffmpeg（音声処理に必要）

#### ffmpegのインストール

このツールは音声処理のために `ffmpeg` を必要とします。

macOSの場合:
```bash
brew install ffmpeg
```

Linuxの場合:
```bash
sudo apt-get install ffmpeg
```

注意: 以前は `pydub` ライブラリを使用していましたが、`pyaudioop` モジュールの互換性の問題により削除されました。現在は `ffmpeg` を直接使用しています。

### セットアップ

1. リポジトリをクローン：

```bash
git clone https://github.com/uzulla/pod-tenuki.git
cd pod-tenuki
```

2. パッケージをインストール：

```bash
pip install -e .
```

3. APIキーを含む`.env`ファイルを作成：

```bash
cp .env.example .env
# .envファイルを編集してAPIキーを追加
```

## 使用方法

### 基本的な使い方

```bash
pod-tenuki /path/to/your/audio_file.mp3
```

これにより以下が実行されます：
1. デフォルトのAuphonicプリセットを使用して音声ファイルを変換
2. Google Gemini APIを使用して変換された音声を文字起こし
3. 文字起こしからポッドキャストのタイトルと説明文を生成

### コマンドラインオプション

```
使用法: pod-tenuki [-h] [--preset-uuid PRESET_UUID] [--preset-name PRESET_NAME]
                  [--output-dir OUTPUT_DIR] [--language LANGUAGE]
                  [--skip-conversion] [--skip-transcription]
                  [--skip-summarization] [--verbose]
                  audio_file

Auphonic、文字起こし、要約でポッドキャスト音声ファイルを処理します。

位置引数:
  audio_file            処理する音声ファイルのパス（MP3、MP4、m4aなど）

オプション引数:
  -h, --help            ヘルプメッセージを表示して終了
  --preset-uuid PRESET_UUID
                        使用するAuphonicプリセットのUUID（デフォルト: xbyREqwaKxENW2n5V2y3mg）
  --preset-name PRESET_NAME
                        使用するAuphonicプリセットの名前（--preset-uuidの代わりに使用可能）
  --output-dir OUTPUT_DIR
                        出力ファイルを保存するディレクトリ（デフォルト: 入力ファイルと同じディレクトリ）
  --language LANGUAGE   文字起こしの言語コード（デフォルト: ja-JP）
  --skip-conversion     Auphonicでの音声変換をスキップ
  --skip-transcription  音声の文字起こしをスキップ
  --skip-summarization  文字起こしの要約をスキップ
  --verbose, -v         詳細なログを有効化
```

### 使用例

#### メインCLIツールの使用：

##### 音声変換のみ：

```bash
pod-tenuki --skip-transcription --skip-summarization audio_file.mp3
```

##### 文字起こしのみ（変換をスキップ）：

```bash
pod-tenuki --skip-conversion --skip-summarization audio_file.mp3
```

##### 既存の文字起こしを要約：

```bash
pod-tenuki --skip-conversion --skip-transcription audio_file.mp3
# 注：audio_file.txtが存在することを前提としています
```

#### 個別のCLIツールの使用：

##### 音声変換のみ：

```bash
pod-tenuki-convert audio_file.mp3
```

##### 文字起こしのみ：

```bash
pod-tenuki-transcribe audio_file.mp3
```

##### 既存の文字起こしを要約：

```bash
pod-tenuki-summarize audio_file.txt
```

#### 出力ディレクトリの指定：

```bash
pod-tenuki --output-dir /path/to/output audio_file.mp3
```

#### 異なるAuphonicプリセットの使用：

```bash
pod-tenuki --preset-uuid YOUR_PRESET_UUID audio_file.mp3
```

#### 文字起こしの言語を指定：

```bash
pod-tenuki --language en-US audio_file.mp3
```

## APIキー

### Auphonic API

1. [auphonic.com](https://auphonic.com/)でAuphonicアカウントを作成
2. [アカウント設定ページ](https://auphonic.com/engine/account/)からAPIキーを取得
3. APIキーを`.env`ファイルに追加：

```
AUPHONIC_API_KEY=your_auphonic_api_key
```

### Gemini API

1. [ai.google.dev](https://ai.google.dev/)でGoogle AI Studioアカウントを作成
2. [APIキーセクション](https://ai.google.dev/api/register)からAPIキーを取得
3. APIキーを`.env`ファイルに追加：

```
GEMINI_API_KEY=your_gemini_api_key
```

### OpenAI API

1. [openai.com](https://openai.com/)でOpenAIアカウントを作成
2. [APIキーセクション](https://platform.openai.com/api-keys)でAPIキーを作成
3. APIキーを`.env`ファイルに追加：

```
OPENAI_API_KEY=your_openai_api_key
```

## 出力ファイル

入力ファイル`podcast.mp3`に対して、以下のファイルが作成されます：

- 変換された音声ファイル：Auphonicプリセット設定に依存
- 文字起こし：`podcast.txt`
- 要約：`podcast.summary.md`

## コスト追跡

アプリケーションは処理終了時にAPI使用コストを追跡して表示します：

```
API使用コスト:
OpenAI API:
  - gpt-3.5-turbo: 1234入力トークン, 567出力トークン, $0.0012
Gemini API:
  - 音声文字起こし: 30.50分, $0.0763
合計コスト: $0.0775
```

これにより、ポッドキャストファイルの処理に関連するコストを監視できます。

## ライセンス

MIT
