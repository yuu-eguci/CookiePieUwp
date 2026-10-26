[![windows-ci](https://github.com/yuu-eguci/CookiePieUwp/actions/workflows/windows-ci.yml/badge.svg?branch=master)](https://github.com/yuu-eguci/CookiePieUwp/actions/workflows/windows-ci.yml)

CookiePieUwp
===

UWP アプリ (C# / .NET Native) のビルドと単体テストを CI で回すための実験用リポジトリ。
アプリ本体は Visual Studio の Blank App テンプレートに `Helpers/Util.AddOne` を足しただけで、追加の機能はない。

- Docker: 非対応 (Windows UWP のため)
- C#: UWP / .NET Native
- Test: MSTest

## 前提環境

| 項目 | 内容 |
| --- | --- |
| OS | Windows 10 1809 (10.0.17763) 以降、または Windows 11 |
| Visual Studio | 2026 (18.x)。ワークロード「ユニバーサル Windows プラットフォーム開発」と .NET Native コンポーネント (CI で確認済み。2022 (17.x) は未確認) |
| Windows SDK | 10.0.26100.0 (`TargetPlatformVersion`)  |
| 最小 OS バージョン | 10.0.17763.0 (`TargetPlatformMinVersion`)  |
| 開発者モード | テスト実行時に署名なしのテストアプリを登録するので必要 |

macOS / Linux ではビルドもテストもできない (Docker の Linux コンテナーも不可) 。

主な NuGet パッケージ:

- `Microsoft.NETCore.UniversalWindowsPlatform` 6.2.14
- `MSTest.TestFramework` / `MSTest.TestAdapter` 3.11.1

## ビルドとテスト

「Developer PowerShell for VS 2026」でリポジトリ直下から実行する。

```powershell
# Debug x64 でアプリとテストをビルド
msbuild CookiePieUwp.sln /restore /p:Configuration=Debug /p:Platform=x64

# テスト実行
vstest.console.exe CookiePieUwp.Tests\bin\x64\Debug\CookiePieUwp.Tests.build.appxrecipe /Platform:x64 /Framework:FrameworkUap10

# Release x64 (.NET Native) でアプリとテストをビルド
msbuild CookiePieUwp.sln /restore /p:Configuration=Release /p:Platform=x64
```

別の Windows SDK を使うときは `/p:TargetPlatformVersion=10.0.xxxxx.0` で上書きできる。

## わざと失敗するテスト (CI 実験用)

もともと `AddOne(1) == 3` という必ず失敗するテストで、CI が失敗を検知できるか試していた。
このテスト (`AddOne_IntentionalFailure`) は通常のビルドには含めず、`IncludeExpectedFailureTest=true` を付けたときだけコンパイルされる。

```powershell
msbuild CookiePieUwp.Tests\CookiePieUwp.Tests.csproj /t:Rebuild /restore /p:Configuration=Debug /p:Platform=x64 /p:IncludeExpectedFailureTest=true
vstest.console.exe CookiePieUwp.Tests\bin\x64\Debug\CookiePieUwp.Tests.build.appxrecipe /Platform:x64 /Framework:FrameworkUap10
```

`AddOne_IntentionalFailure` の 1 件だけが失敗すれば期待どおり。
確認が終わったら、`IncludeExpectedFailureTest` なしで `/t:Rebuild` し直す (付けたままだと次のテスト実行でも失敗する) 。

## CI

### GitHub Actions (`.github/workflows/windows-ci.yml`)

`windows-2025-vs2026` ランナーで、master への push、pull request、手動実行のときに動く。

1. TRX 検査スクリプト (`tools/ci/check_trx.py`) の単体テスト
2. 開発者モードが有効か確認 (読み取りのみ。ランナーの設定は変更しない)
3. Debug x64 でビルドしてテスト実行。実行件数が 0 件、または失敗が 1 件でもあればエラー
4. わざと失敗するテストを入れて再ビルドし、`AddOne_IntentionalFailure` だけが失敗することを確認
5. Release x64 (.NET Native) でアプリとテストをビルド

### Azure Pipelines (`azure-pipelines.yml`)

自動トリガーは無効 (`trigger: none` / `pr: none`) で、手動実行専用。
Azure DevOps 側の画面でトリガーが上書き設定されていないかは未確認。

## 未検証のこと・制限

- CI で確認しているのは x64 の Debug / Release ビルドと Debug x64 での UWP テスト実行だけ。Release (.NET Native) でのテスト実行は CI ではしていない。
- GUI の起動、実機での動作、x86 / ARM / ARM64 のビルドは未確認。
- Windows Server のランナーでは GUI の確認やデバッグはできない。
- パッケージ署名は無効 (`AppxPackageSigningEnabled=false`) 。Store 提出や配布は行わない。
- .NET Native は新機能が追加されず、Visual Studio 2026 の C# UWP の既定は modern .NET (Native AOT) 。このリポジトリは移行していない。
