#coding: utf-8

import hashlib
import json
from urllib.parse import urlparse

from textwrap import dedent
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request

import requests


class Blockchain(object):
    def __init__(self):
        # チェーン
        self.chain = []
        # トランザクションのリスト
        self.current_transactions = []

        # ノード（取引者）のリスト
        # 「セット」は要素に重複のないリストを保持するPythonのデータ形式
        self.nodes = set()

        # ジェネシスブロック（先祖を持たないブロック）
        self.new_block(proof=100, previous_hash=1)

    def new_block(self, proof, previous_hash=None):
        # 新しいブロックを作り、チェーンに加える
        """
        ブロックチェーンに新しいブロックを作る
        :param proof: <int> プルーフ。プルーフ・オブ・ワークアルゴリズム（正当な取引を照明するための手続き）から得られる
        :param previous_hash: (option) <str> 前のブロックのハッシュ
        :return: <dict> 新しいブロック
        """

        # 新しいブロックを作る
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # 現在のトランザクションリストをリセット
        # トランザクションを持つブロックが決まったため
        self.current_transactions = []

        # 作った新しいブロックをチェーンに加える
        self.chain.append(block)
        # 作った新しいブロックを返す
        return block

    def new_transaction(self, sender, recipient, amount):
        # 新しいトランザクションをリストに加える

        """
        次に採掘されるブロックに加えるための新しいトランザクションを作る
        :param sender: <str> 送信者のアドレス
        :param recipient: <str> 受信者のアドレス
        :param amount: <int> 取引量
        :return: <int> このトランザクションを持つブロックのアドレス
        """

        # 新しいトランザクションを作りトランザクションのリストに加える
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        # このトランザクションが加えられるブロック（次に採掘されるブロック）のインデックスを返す
        return self.last_block['index'] + 1

    def register_node(self, address):
        """
        ノードのリストに新しいノードを加える
        :param address: <str> ノードのアドレス 例: 'http://192.168.0.5:5000'
        :return: None
        """

        parse_url = urlparse(address)
        self.nodes.add(parse_url.netloc) # .netlocは"example.com"のような形の<str>

    @staticmethod
    def hash(block):
        # ブロックをハッシュ化する
        """
        ブロックのSHA-256ハッシュを作る
        :param block: <dict> ハッシュを作るブロック
        :return: <str> ハッシュ
        """

        # 必ずブロックのディクショナリをソートすることで、一貫性のあるハッシュを作る
        block_string = json.dumps(block, sort_keys=True).encode()
        # ダイジェスト（作成されたSHA-256ハッシュ）を返す
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # チェーンの最後のブロックを返す
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        シンプルなプルーフ・オブ・ワークのアルゴリズム
        - hash(pp')の最初の4つが0となるようなp'を探す
        - pは前のプルーフ、p'は新しいプルーフ
        :param last_proof: <int> 前のプルーフ
        :return: <int> 新しいプルーフ
        """

        proof = 0 # 新しいプルーフ
        # プルーフが条件を満たす（正しい）までプルーフをインクリメントし続ける
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        プルーフが正しいか確認する: hash(last_proof+proof)の最初の4つが0となっているか？
        :param last_proof: <int> 前のプルーフ
        :param proof: <int> 現在のプルーフ
        :return: <bool> プルーフが正しければTrue、そうでなければFalse
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        # 最初の4つが"0000"ならTrueを返す
        return guess_hash[:4] == "0000"

    def valid_chain(self, chain):
        """
        ブロックチェーンが正しいか確認する
        :param chain: <list> ブロックチェーン
        :return: <bool> 正しければTrue、そうでなければFalse
        """

        last_block = chain[0]
        current_index = 1

        # index=1（2つ目のブロック）から最後のブロックまでたどる
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n------------\n")

            # ブロックのハッシュ値が正しいか確認する
            # ブロックの'previous_hash'が直前のブロックをハッシュ化したものと一致しなければFalse
            if block['previous_hash'] != self.hash(last_block):
                return False

            # プルーフ・オブ・ワークが正しいか確認する
            # ブロックの'proof'と直前のブロックの'proof'の組み合わせでプルーフ・オブ・ワークが正しくなければFalse
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        コンセンサスアルゴリズム。ネットワーク上の最も長いチェーンをもって正しいチェーンとし、自らのチェーンをその最長チェーンに置き換えることでコンフリクトを解消する
        :return: <bool> 自らのチェーンが置き換えられたときTrue、そうでなければFalse
        """

        neigbours = self.nodes
        new_chain =None

        # 自らのチェーンより長いチェーンを探していく
        max_length = len(self.chain) # 自らのチェーンの長さ

        # 他のすべてのノードの持つチェーンの長さを確認する
        for node in neigbours:
            # self.nodesの各要素は"example.com"の形をしている
            # GETメソッドで"http://example.com/chain"をリクエストし、ノードの持つチェーンを取得する
            response = requests.get(f'http://{node}/chain')

            # リクエストが成功しチェーンを取得できていれば
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # そのチェーンが有効かつそれまでのチェーンより長いかを確認する
                if self.valid_chain(chain) and length > max_length:
                    max_length = length
                    new_chain = chain

        # もし有効かつ自らのチェーンより長くチェーンを見つけた場合、そのチェーンで自らのチェーンを置き換える
        if new_chain:
            self.chain = new_chain
            return True

        return False



# ノードを作る
app = Flask(__name__)

# 作成したノードのユニークなアドレスを作る
node_indentifire = str(uuid4()).replace('-', '')

# ブロックチェーンクラスをインスタンス化する
blockchain = Blockchain()

# 新しいトランザクションを作るメソッド
# POSTメソッドで/transaction/newエンドポイントを作る。POSTメソッドなのでデータを送信する
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # POSTされたデータに必要なデータがそろっているか確認する
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        # POSTの形式が誤っていればHTTP 400 Bad Requestを返す
        return 'Missing values', 400

    # 新しいトランザクションを作る
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'トランザクションはブロック{index}に追加されました'}
    # リクエストが成功しリソースが作成されたのでHTTP 201 Createdを返す
    return jsonify(response), 201

# 新しいブロックを採掘するメソッド
# GETメソッドで/mineエンドポイントを作る
@app.route('/mine', methods=['GET'])
def mine():
    # プルーフ・オブ・ワークアルゴリズムを実行し新しいプルーフを見つける
    # プルーフ・オブ・ワークアルゴリズムは最新のプルーフを参照する
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # プルーフを見つけたことに対する報酬を得る
    # 新しいコインを採掘したことを表すためsenderは"0"とする
    blockchain.new_transaction(
        sender="0",
        recipient=node_indentifire,
        amount=1
    )

    # 見つけたプルーフを利用してチェーンに新しいブロックを加え、新しいブロックを採掘する
    block = blockchain.new_block(proof)

    response = {
        'message': "新しいブロックを採掘しました",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    # リクエストが成功したのでHTTP 200 OKを返す
    return jsonify(response), 200

# インターネット上に新しいノードを追加するメソッド
# リクエストはノードのアドレスのリストで与えるものとする 例: {["http://192.168.0.5:5000"]}
@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        # POSTの形式が間違っていれば、HTTP 400 Bad Requestを返す
        return "Error: 有効ではないノードのリストです", 400

    # リクエストに含まれるノードを自らの持つノードリストに加える
    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': "新しいノードが追加されました",
        'total_nodes': list(blockchain.nodes)
    }
    # リクエストが成功しリソースが作成されたのでHTTP 201 Createdを返す
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    # コンフリクトを解消する
    # 自らの持っていたチェーンが最長でなく置き換えられた場合True
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': "チェーンが置き換えれらました",
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': "チェーンは確認されました",
            'chain': blockchain.chain
        }

    #リクエストが成功したのでHTTP 200 OKを返す
    return jsonify(response), 200

# ブロックチェーン全体を返すメソッド
# GETメソッドで/chainエンドポイントを作る
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

# ポートを指定してサーバを起動する
if __name__ == '__main__':
    print("ポートを整数で指定してください　例：5000")
    port = input('>>')
    app.run(host='0.0.0.0', port=port)