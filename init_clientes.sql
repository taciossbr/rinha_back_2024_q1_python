CREATE TABLE clientes (
    id INT PRIMARY KEY,
    limite INTEGER NOT NULL,
    saldo INTEGER NOT NULL DEFAULT '0'
    -- TODO ver se o INTEGER e suficiente
);

CREATE TYPE tipo_transacao AS ENUM ('c', 'd');
CREATE TABLE transacoes(
    id SERIAL PRIMARY KEY, -- TODO ver se precisa disso
    valor INTEGER NOT NULL,
    tipo tipo_transacao NOT NULL,
    descricao VARCHAR(10) NOT NULL,
    realizada_em TIMESTAMP NOT NULL DEFAULT NOW(),
    cliente_id INT NOT NULL REFERENCES clientes(id)
);

INSERT INTO clientes VALUES
('1', '100000', '0'),
('2', '80000', '0'),
('3', '1000000', '0'),
('4', '10000000', '0'),
('5', '500000', '0');

