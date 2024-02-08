import logging
from typing import Any, Dict
from flask import Flask, jsonify, request
import psycopg
from psycopg.rows import dict_row
import psycopg_pool
import os

app = Flask(__name__)

db_pool = psycopg_pool.ConnectionPool(
    os.environ.get('DATABASE_URL'),
    min_size=4, max_size=10
)


@app.get('/hello')
def hello():
    with db_pool.connection() as conn:
        rec = conn.execute('SELECT * FROM clientes')
        print(rec.fetchall())
        return 'hello, world'


@app.post('/clientes/<cliente_id>/transacoes')
def add_transacao(cliente_id: str):
    cliente_id = int(cliente_id)
    data: Dict[str, Any] = request.json

    # TODO valor pode ser negativo ?
    if not (valor := data.get('valor')) or not isinstance(valor, int):
        return jsonify(error='valor invalido'), 422
    if not (tipo := data.get('tipo')) or not tipo in ['c', 'd']:
        return jsonify(error='tipo invalido'), 422
    if not (descricao := data.get('descricao')) or len(descricao) > 10:
        return jsonify(error='descricao invalida'), 422

    if cliente_id < 0 or cliente_id > 5:
        return jsonify(error='nao encontrado'), 404

    try:
        with db_pool.connection() as conn:
            cur = conn.execute(
                'CALL insert_transacao(%s, %s, %s, %s)',
                (valor, tipo, descricao, cliente_id))
            resul = cur.fetchone()
            saldo, limite = resul

            return jsonify(saldo=saldo, limite=limite)
    # except NotFound:
    #     return jsonify(error='nao encontrado'), 404
    # except SaldoInsuficiente:
    #     return jsonify(error='saldo insuficiente'), 422
    except psycopg.errors.InvalidTransactionTermination:
        return jsonify(error='saldo insuficiente'), 422


@app.get('/clientes/<cliente_id>/extrato')
def extrato(cliente_id: str):
    cliente_id = int(cliente_id)

    # if cliente_id < 0 or cliente_id > 5:
    #     return jsonify(error='nao encontrado'), 404

    with db_pool.connection() as conn:
        cur = conn.cursor(row_factory=dict_row)
        cur_saldo = cur.execute(
            '''
            SELECT limite, saldo AS total, NOW() as data_extrato
            FROM clientes 
            WHERE id = %s''',
            (cliente_id,))
        if cur_saldo.rowcount == 0:
            return jsonify(error='nao encontrado'), 404
        saldo = cur_saldo.fetchone()

        cur_transacoes = cur.execute(
            '''
            SELECT valor, tipo, descricao, realizada_em FROM transacoes
            WHERE cliente_id = %s
            ORDER BY realizada_em DESC
            LIMIT 10
            ''',
            (cliente_id,))
        transacoes = cur_transacoes.fetchall()

        # TODO datas estao indo com uma formatacao errada
        return jsonify(
            saldo=saldo,
            ultimas_transacoes=transacoes)


class NotFound(Exception):
    ...


class SaldoInsuficiente(Exception):
    ...
