import logging
from typing import Any, Dict
from flask import Flask, jsonify, request
import psycopg
from psycopg.rows import dict_row
import psycopg_pool
import os

app = Flask(__name__)

db_pool = psycopg_pool.AsyncConnectionPool(
    os.environ.get('DATABASE_URL'),
    min_size=20, max_size=250,

    open=False
)


@app.post('/clientes/<cliente_id>/transacoes')
async def add_transacao(cliente_id: str):
    await db_pool.open(True)
    cliente_id = int(cliente_id)
    data: Dict[str, Any] = request.json

    # TODO valor pode ser negativo ?
    if not (valor := data.get('valor')) or not isinstance(valor, int):
        return jsonify(error='valor invalido'), 422
    if not (tipo := data.get('tipo')) or not tipo in ['c', 'd']:
        return jsonify(error='tipo invalido'), 422
    if not (descricao := data.get('descricao')) or len(descricao) > 10:
        return jsonify(error='descricao invalida'), 422

    async with db_pool.connection() as conn:
        cur = await conn.execute(
            'CALL insert_transacao(%s, %s, %s, %s)',
            (valor, tipo, descricao, cliente_id))
        result = await cur.fetchone()
        saldo, limite, status = result
        match status:
            case 422:
                return jsonify(error='saldo insuficiente'), 422
            case 404:
                return jsonify(error='nao encontrado'), 404

        return jsonify(saldo=saldo, limite=limite)


@app.get('/clientes/<cliente_id>/extrato')
async def extrato(cliente_id: str):
    await db_pool.open(True)
    cliente_id = int(cliente_id)

    async with db_pool.connection() as conn:

        await conn.execute(
            "CALL extrato(%s, 'cliente', 'transacoes')",
            (cliente_id,))

        cur_saldo = conn.cursor(
            'cliente', row_factory=dict_row)
        saldo = await cur_saldo.fetchone()
        if not saldo:
            return jsonify(error='nao encontrado'), 404

        cur_transacoes = conn.cursor(
            'transacoes',
            row_factory=dict_row)
        transacoes = await cur_transacoes.fetchall()

        return jsonify(
            saldo=saldo,
            ultimas_transacoes=[
                {**tr, 'realizada_em': tr['realizada_em'].isoformat()}
                for tr in transacoes
            ])


class NotFound(Exception):
    ...


class SaldoInsuficiente(Exception):
    ...
