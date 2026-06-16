# 配布前チェックリスト

Inno Setup インストーラー化前後の確認済み項目です。

## 1. ビルド前確認

- [x] `python -m pytest` が全件成功する
- [x] `requirements.txt` に必要な依存関係が含まれている
- [x] `meeting_cost_timer.spec` がプロジェクト直下に存在する
- [x] `meeting_cost_timer.spec` の `datas` に `app/ui` が含まれている
- [x] `app/icons` / `templates` は実ファイルがない場合、同梱対象にしていない
- [x] `__pycache__` を同梱対象にしていない
- [x] 既存の `dist/meeting_cost_timer` を削除してから再ビルドする

確認結果:

- 実行コマンド: `python -m pytest`
- 結果: `263 passed`

## 2. PyInstallerビルド確認

- [x] `python -m PyInstaller meeting_cost_timer.spec` が成功する
- [x] `dist/meeting_cost_timer/meeting_cost_timer.exe` が生成される
- [x] ビルドログに致命的なエラーが出ていない
- [x] `dist/meeting_cost_timer/_internal/app/ui` が生成される
- [x] `dist/meeting_cost_timer/_internal/app/ui` 配下に `.ui` ファイルが15件含まれる

確認結果:

- 実行前処理: 既存の `dist/meeting_cost_timer` を削除
- 実行コマンド: `python -m PyInstaller meeting_cost_timer.spec`
- 結果: `Build complete`
- 生成EXE: `dist/meeting_cost_timer/meeting_cost_timer.exe`
- 同梱UI: `dist/meeting_cost_timer/_internal/app/ui`

## 3. EXE起動確認

- [x] `dist/meeting_cost_timer/meeting_cost_timer.exe` を起動できる
- [x] 初回起動時にライセンス・端末設定画面が表示される
- [x] ライセンスIDと端末種別を保存できる
- [x] 設定済みの場合、メインメニューが表示される
- [x] `.ui` 読込エラーが発生しない
- [x] 起動時に不要な例外ダイアログが表示されない

確認結果:

- 初回表示: `ライセンス・端末設定`
- 保存後表示: `メインメニュー`
- `.ui` 読込エラー: なし

## 4. 主要画面遷移確認

- [x] メインメニューから会議開始設定画面へ遷移できる
- [x] メインメニューからマスタ管理メニューへ遷移できる
- [x] メインメニューから表示設定画面へ遷移できる
- [x] メインメニューからライセンス・端末設定画面へ遷移できる
- [x] 各画面の閉じる操作で想定どおり前画面へ戻れる
- [x] 画面遷移時に不要なエラーが発生しない

確認結果:

- 確認画面: `メインメニュー`, `マスタメニュー`, `表示設定`, `会議開始設定`
- 画面遷移エラー: なし

## 5. カウント動作確認

- [x] 会議開始設定画面で会議名を入力できる
- [x] 算出方式を選択できる
- [x] 合算時間単価が設定された状態でカウント表示画面へ進める
- [x] カウント表示画面で開始できる
- [x] 一時停止でカウント加算が停止する
- [x] 再開でカウント加算が再開する
- [x] 終了でカウントが終了する
- [x] 終了時に結果出力確認ダイアログが表示される
- [x] No選択時に結果出力画面へ遷移しない
- [x] Yes選択時に結果出力画面へ遷移する

確認結果:

- 確認操作: `開始` → `一時停止` → `再開` → `終了`
- 結果出力確認: 表示あり
- Yes選択後: `結果出力` 画面表示

## 6. CSV出力確認

- [x] 結果出力画面で出力先フォルダを指定できる
- [x] CSV出力を実行できる
- [x] CSVファイル名が `meeting_cost_YYYYMMDD_HHMMSS.csv` 形式で作成される
- [x] CSVがUTF-8 BOM付きで出力される
- [x] CSV出力項目が仕様上の項目に限定されている
- [x] 参加者別明細が出力されていない
- [x] 個別単価が出力されていない
- [x] 役職人数内訳が出力されていない
- [x] 算出方式が日本語表示で出力される
- [x] `precise` は `精密モード` として出力される
- [x] `simple` は `簡易モード` として出力される
- [x] `direct` は `直接入力` として出力される
- [x] `display_data` は `表示用データ` として出力される

確認結果:

- EXE確認CSV: `dist/meeting_cost_timer/manual_check_output/meeting_cost_20260605_162508.csv`
- インストール後確認CSV: `C:\Users\takes\AppData\Local\Programs\MeetingCostTimerInstallCheck\install_check_output\meeting_cost_20260605_165923.csv`
- CSV確認内容:

```csv
会議名,算出方式,開始日時,終了日時,実カウント時間,合算時間単価,会議コスト
Installer CSV Check,精密モード,2026-06-05T16:59:20.617818,2026-06-05T16:59:22.122951,1,1,0
```

## 7. ログ確認

- [x] `dist/meeting_cost_timer/logs/error.log` が作成される
- [x] 正常操作時に不要なエラーが出力されない
- [x] 例外発生時に `logs/error.log` へ記録される
- [x] ログに会議名が含まれない
- [x] ログに参加者情報が含まれない
- [x] ログに個別単価が含まれない
- [x] ログに役職人数内訳が含まれない
- [x] print出力に依存していない

確認結果:

- インストール後ログ: `C:\Users\takes\AppData\Local\Programs\MeetingCostTimerInstallCheck\logs\error.log`
- 結果: `error.log` は空

## 8. 設定保存確認

- [x] 初回起動時に、EXE配置フォルダ基準の `config/app_settings.json` が作成される
- [x] ライセンスIDが保存される
- [x] 端末種別が保存される
- [x] CSV出力後、前回出力先が保存される
- [x] 再起動後に保存済み設定が読み込まれる
- [x] 設定ファイル破損時に退避処理が行われる
- [x] 設定保存・読込で不要なエラーが発生しない

確認結果:

- インストール後設定: `C:\Users\takes\AppData\Local\Programs\MeetingCostTimerInstallCheck\config\app_settings.json`
- 作成結果: あり
- 保存確認: ライセンスID、端末種別、前回出力先

## 9. 同梱ファイル確認

- [x] `meeting_cost_timer.exe` が含まれている
- [x] `_internal` フォルダが含まれている
- [x] `_internal/app/ui` 配下に必要な `.ui` ファイルが含まれている
- [x] PyQt6実行に必要なファイルが含まれている
- [x] `cryptography` 実行に必要なファイルが含まれている
- [x] EXE単体ではなく、`dist/meeting_cost_timer` フォルダ一式で動作確認する

確認結果:

- インストール先: `C:\Users\takes\AppData\Local\Programs\MeetingCostTimerInstallCheck`
- インストール後ファイル数: `194`
- `_internal/app/ui`: あり

## 10. 配布対象外ファイル確認

- [x] `build` フォルダを配布対象に含めない
- [x] `.pytest_cache` を配布対象に含めない
- [x] `__pycache__` を配布対象に含めない
- [x] テストファイルを配布対象に含めない
- [x] ソースコード一式を配布対象に含めない
- [x] 開発用ログや確認用CSVを配布対象に含めない
- [x] `manual_check_output` を配布対象に含めない
- [x] `.spec` ファイルを配布対象に含めない
- [x] `.git` フォルダを配布対象に含めない

確認結果:

- Inno Setup対象: `dist/meeting_cost_timer` フォルダ一式
- インストーラー生成物: `installer/meeting_cost_timer_setup.exe`
- インストーラーサイズ: `34,603,732` bytes

## 11. Inno Setupコンパイル確認

- [x] `ISCC.exe` の場所を確認する
- [x] `meeting_cost_timer.iss` のコンパイルが成功する
- [x] インストーラーEXEが生成される
- [x] 生成インストーラーでインストールできる
- [x] インストール後に `meeting_cost_timer.exe` が起動する
- [x] インストール先に `config` / `logs` が作成される
- [x] インストール後EXEでCSV出力まで動作する

確認結果:

- `ISCC.exe`: `C:\Users\takes\AppData\Local\Programs\Inno Setup 6\ISCC.exe`
- 実行コマンド: `ISCC.exe .\meeting_cost_timer.iss`
- 結果: `Successful compile`
- 生成インストーラー: `installer/meeting_cost_timer_setup.exe`
- テスト用インストール先: `C:\Users\takes\AppData\Local\Programs\MeetingCostTimerInstallCheck`
