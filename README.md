# ota_blockchain
ブロックチェーンを作ることで学ぶ 〜ブロックチェーンがどのように動いているのか学ぶ最速の方法は作ってみることだ〜[ https://qiita.com/hidehiro98/items/841ece65d896aeaa8a2a ]を実装した

# 詳細
blockchain.py - 本体．実行するとそのPC上にWebアプリケーションとして起動する．
PoW.py - ブロックチェーンにおいて取引の認証を担っている「プルーフ・オブ・ワーク」アルゴリズムの例．本体とは関係ない．


# 使い方
**使ってみるより自ら実装してみることを推奨します**

1. コマンドラインからblockchain.pyを実行．ポート番号を指定して起動．

```
C:\Users\~ py blockchain.py
```

2. [Postman](https://www.getpostman.com)等からHTTPリクエストを送る．POSTの形式等は元記事もしくはblockchain.pyのコメント参照．

- [GET] /mine : 新しいコインを採掘する
- [POST] /transaction/new : 新しい取引を作成する
- [POST] /nodes/register : 新しいノード（取引者）を登録する
- [GET] /nodes/resolve : 取引記録を確認し最新の状態にする
- [GET] /chain : ブロックチェーン全体を取得する