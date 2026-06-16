# リリースメモ

## 1. リリース対象

- アプリ名: 会議コストタイマー
- バージョン: 1.0.0
- 対象OS: Windows
- 配布形式: Inno Setup インストーラー
- アプリ形式: Windows向けスタンドアロンアプリ

## 2. 主な機能

- 会議名、算出方式、合算時間単価を指定して会議コストをカウント
- 精密モード、簡易モード、直接入力、表示用データ読込に対応
- カウントの開始、一時停止、再開、終了に対応
- 終了後の確認ダイアログからCSV出力画面を表示
- 直近1回分の会議結果をCSV出力
- ライセンスIDと端末種別の設定保存
- 参加者マスタ、役職単価マスタの保存・読込
- 表示用データの読込
- マスタ取込、マスタ出力
- エラー発生時の `logs/error.log` 出力

## 3. 今回確認済みの動作

- PyInstaller によるEXEビルド成功
- `dist/meeting_cost_timer/meeting_cost_timer.exe` の起動確認
- `app/ui` 配下の `.ui` ファイル読込確認
- 初回起動時のライセンス・端末設定画面表示
- ライセンスID、端末種別の保存確認
- メインメニュー表示確認
- 会議開始設定画面への遷移確認
- カウント表示画面への遷移確認
- カウントの開始、終了確認
- 終了後の結果出力確認ダイアログ表示
- Yes選択時の結果出力画面表示
- CSV出力成功
- CSVの算出方式が日本語表示で出力されることを確認
- Inno Setup によるインストーラー作成成功
- 生成インストーラーからのインストール成功
- インストール後EXEの起動確認
- インストール先に `config/app_settings.json` と `logs/error.log` が作成されることを確認
- 正常操作時に `logs/error.log` が空であることを確認
- `python -m pytest` 全件成功

## 4. 配布物

- インストーラー:
  - `installer/meeting_cost_timer_setup.exe`
- インストールされる主なファイル:
  - `meeting_cost_timer.exe`
  - `_internal` フォルダ一式
  - `_internal/app/ui` 配下の `.ui` ファイル
- 実行時に作成される主なファイル:
  - `config/app_settings.json`
  - `logs/error.log`

## 5. 既知の制限

- Excel出力は未対応
- アプリ内履歴保存は行わない仕様
- CSV出力は直近1回分の会議結果のみ対象
- CSVには参加者別明細、個別単価、役職人数内訳は出力しない
- EXE配置フォルダ基準で `config` / `logs` を作成するため、書き込み可能な場所へインストールする必要がある

## 6. 注意事項

- 配布前は `dist/meeting_cost_timer` を削除してから PyInstaller ビルドを実行する
- 配布対象は Inno Setup で生成した `installer/meeting_cost_timer_setup.exe`
- `build`、`.pytest_cache`、`__pycache__`、テストファイル、ソースコード一式は配布対象外
- 確認用CSVや開発用ログは配布対象外
- `logs/error.log` には会議名、参加者情報、個別単価、役職人数内訳などの機密性がある情報を含めない
