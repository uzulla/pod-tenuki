# Pod-Tenuki

Pod-Tenukiは、ポッドキャストの音声ファイルを処理するためのコマンドラインツールです。以下の機能を提供します：

1. **音声変換**: Auphonic APIを使用して音声ファイル（MP3、MP4、m4aなど）を指定のプリセットで変換
2. **WAVファイル連結**: 複数のWAVファイルを1つのMP3ファイルに連結
3. **文字起こし**: Google Cloud Speech-to-Text APIを使用して音声ファイルをテキストに変換（最大8時間の長時間音声に対応）
4. **要約**: OpenAI APIを使用して文字起こしからポッドキャストのタイトルと説明文を生成
5. **コスト追跡**: Google Cloud Speech-to-TextとOpenAI APIの使用コストを追跡して表示（使用した分数と料金）

## インストール

### 前提条件

- Python 3.8以上
- Auphonic APIキー
- Google Cloud Platform アカウントと認証情報
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

複数のWAVファイルの処理：
```bash
pod-tenuki /path/to/recording1.wav /path/to/recording2.wav /path/to/recording3.wav
```

この場合は以下が実行されます：
1. 複数のWAVファイルが自動的に1つのMP3ファイルに連結
2. 連結されたファイルに対して通常の処理が実行される

### コマンドラインオプション

```
使用法: pod-tenuki [-h] [--preset-uuid PRESET_UUID] [--preset-name PRESET_NAME]
                  [--output-dir OUTPUT_DIR] [--output-name OUTPUT_NAME]
                  [--language LANGUAGE] [--skip-conversion] [--skip-transcription]
                  [--skip-summarization] [--verbose]
                  audio_files [audio_files ...]

Auphonic、文字起こし、要約でポッドキャスト音声ファイルを処理します。

位置引数:
  audio_files           処理する音声ファイルのパス（MP3、MP4、m4a、WAV など）。複数のWAVファイルは連結されます。

オプション引数:
  -h, --help            ヘルプメッセージを表示して終了
  --preset-uuid PRESET_UUID
                        使用するAuphonicプリセットのUUID（デフォルト: xbyREqwaKxENW2n5V2y3mg）
  --preset-name PRESET_NAME
                        使用するAuphonicプリセットの名前（--preset-uuidの代わりに使用可能）
  --output-dir OUTPUT_DIR
                        出力ファイルを保存するディレクトリ（デフォルト: 入力ファイルと同じディレクトリ）
  --output-name OUTPUT_NAME
                        複数のファイルを連結する際の出力ファイル名
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

##### 複数のWAVファイルを連結して処理：

```bash
pod-tenuki recording1.wav recording2.wav recording3.wav
```

これにより以下の処理が行われます：
1. WAVファイルが自動的に一時的なMP3ファイルに連結
2. 連結されたファイルをAuphonicで処理
3. 文字起こしと要約の生成

##### 複数のWAVファイルの連結と文字起こしのみ：

```bash
pod-tenuki --skip-conversion --skip-summarization recording1.wav recording2.wav recording3.wav
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

複数のWAVファイルを連結して変換：
```bash
pod-tenuki-convert recording1.wav recording2.wav recording3.wav
```

##### 文字起こしのみ：

```bash
pod-tenuki-transcribe audio_file.mp3
```

複数のWAVファイルを連結して文字起こし：
```bash
pod-tenuki-transcribe recording1.wav recording2.wav recording3.wav
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

### Google Cloud Speech-to-Text API

1. Google Cloud Platform (GCP) プロジェクトを設定する：
   - [Google Cloud コンソール](https://console.cloud.google.com/)にアクセスし、Googleアカウントでログイン
   - 新しいプロジェクトを作成（または既存のプロジェクトを選択）
   - 「API とサービス」→「ライブラリ」から以下のAPIを有効化：
     - Cloud Speech-to-Text API
     - Cloud Storage API（長時間音声の処理に必要）

2. サービスアカウントと認証情報を作成：
   - 「IAM と管理」→「サービスアカウント」で新しいサービスアカウントを作成
   - 以下の権限を付与（必須）：
     - Speech to Text ユーザー
     - Storage オブジェクト管理者（Storage Object Admin）
       （または次の個別権限すべて: Storage オブジェクト作成者・閲覧者・削除者）
   - サービスアカウントの「アクション」メニューから「鍵を管理」→「新しい鍵を作成」→「JSON」を選択し、キーファイルをダウンロード

   重要: サービスアカウントは最低でも以下の権限が必要です:
   - storage.objects.create（ファイルのアップロード）
   - storage.objects.get（ファイルのアクセス）
   - storage.objects.delete（ファイルの削除）

3. Cloud Storage バケットを作成（必須）：
   - 「Cloud Storage」→「バケット」から新しいバケットを作成
   - グローバルに一意な名前を設定（例：`your-project-speech-to-text`）
   - このバケットは長時間音声の一時保存に使用されます
   - バケット名は必ず `.env` ファイルの `GOOGLE_STORAGE_BUCKET` に設定してください
   
   バケット内のファイルを自動削除するには（推奨）：
   - バケットの詳細ページで「ライフサイクル」タブを選択
   - 「ルールを追加」をクリック
   - 以下の設定でルールを作成：
     - 「条件」セクションで「年齢」を選択し、値を「1」日に設定
     - 「アクション」セクションで「削除」を選択
     - 「作成」をクリック
   - これにより、アップロードから1日後にすべてのファイルが自動的に削除されます

4. バケット使用状況の確認方法：
   - 処理中にエラーが発生した場合、以下のコマンドでGCSバケットを確認できます（gcloudコマンドラインツールが必要）：
   ```bash
   gcloud storage ls gs://your-bucket-name
   ```
   - または Google Cloud Console の「Cloud Storage」→「ブラウザ」→バケット名をクリックして確認できます
   - バケットに残っているファイルは、ライフサイクルポリシーに従って自動削除されるか、手動で削除できます

5. APIキーを`.env`ファイルに追加：

```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/downloaded-key-file.json
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_STORAGE_BUCKET=your-storage-bucket-name
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

複数のWAVファイルを入力した場合（例: `recording1.wav`, `recording2.wav`）：

- 連結されたMP3ファイル：一時ディレクトリまたは指定された出力ディレクトリに作成
- 連結ファイルから生成される出力ファイル：上記と同様

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
