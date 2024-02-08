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
    data: Dict[str, Any] = request.json

    # TODO valor pode ser negativo ?
    if not (valor := data.get('valor')) or not isinstance(valor, int):
        return jsonify(error='valor invalido'), 422
    if not (tipo := data.get('tipo')) or not tipo in ['c', 'd']:
        return jsonify(error='tipo invalido'), 422
    if not (descricao := data.get('descricao')) or len(descricao) > 10:
        return jsonify(error='descricao invalida'), 422

    try:
        with db_pool.connection() as conn:
            with conn.transaction() as trx:
                cur = conn.cursor()
                cur.execute(
                    'SELECT pg_advisory_xact_lock(id) FROM clientes WHERE id = %s',
                    (cliente_id,))

                cliente_cur = cur.execute(
                    'SELECT limite, saldo FROM clientes WHERE id = %s',
                    (cliente_id,)
                )
                if cliente_cur.rowcount == 0:
                    raise NotFound()
                result = cliente_cur.fetchone()
                limite, saldo = result

                if tipo == 'c':
                    cur.execute(
                        '''
                        UPDATE clientes
                        SET saldo = saldo + %s
                        WHERE id = %s
                        RETURNING saldo, limite''',
                        (valor, cliente_id))
                elif tipo == 'd':
                    if saldo - valor < -limite:
                        raise SaldoInsuficiente()
                    cur.execute(
                        '''
                        UPDATE clientes
                        SET saldo = saldo - %s
                        WHERE id = %s
                        RETURNING saldo, limite''',
                        (valor, cliente_id))

                cur.execute(
                    '''
                    INSERT INTO transacoes
                    (valor, tipo, descricao, cliente_id)
                    VALUES
                    (%s, %s, %s, %s)''',
                    [valor, tipo, descricao, cliente_id]
                )

                return jsonify(saldo=saldo, limite=limite)
    except NotFound:
        return jsonify(error='nao encontrado'), 404
    except SaldoInsuficiente:
        return jsonify(error='saldo insuficiente'), 422


@app.get('/clientes/<cliente_id>/extrato')
def extrato(cliente_id: str):
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
