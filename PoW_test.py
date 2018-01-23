# プルーフ・オブ・ワークのアルゴリズムを体験する
#coding: utf-8

from hashlib import sha256


x = 5
y = 0 # はじめにはyは未知

# xかけるyの答えのハッシュが0で終わらなければならないというルールが与えられている
# 実際にハッシュを求め、0で終わるようになるまでyをインクリメントし続ける
while sha256(f'{x*y}'.encode()).hexdigest()[-1] != "0":
    y += 1

print(sha256(f'{x*y}'.encode()).hexdigest())
print(f'The solution is [y = {y}]')
# x=0のとき答えはy=21
# 答えを探すのにとにかく計算量を費やすしかないような問題設定になっている