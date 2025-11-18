param(
    [string]$config,
    [string]$domain,
    [string]$record_name,
    [string]$token,
    [switch]$dry_run
)

# プロジェクトルート
$commandPath = $MyInvocation.MyCommand.path
$projectRoot = Split-Path $commandPath -Parent

# venv をアクティベート
. "$projectRoot\.venv\Scripts\Activate.ps1"

# Python スクリプトのパス
$script = Join-Path $projectRoot "vd-update-dns-txt.py"

# 引数組み立て
$argv = @(
    "--config", $config
    "--domain", $domain
    "--record-name", $record_name
    "--token", $token
)

if ($dry_run) {
    $argv += "--dry-run"
}

# 実行
python $script @argv
