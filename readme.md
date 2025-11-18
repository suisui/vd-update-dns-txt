# win-acme (wacs) を使って value domain で証明書更新

## 準備

### python3 が使えるように準備する


### venv 環境作成

```
git clone ...
cd vd-update-dns-txt
python3 -m venv .venv
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### 設定ファイル作成

vdapi の　api_key を作成しておく。

app-config.ini ファイルを作成

``` app-config.ini
[valudomain]
  api_key=***********************
```


### フォルダ作成

``` .sh
mkdir certs
```

### wacs-sample.ps1 を参考に wacs を呼び出す

* ドメイン名
* メールアドレス

を変更する
