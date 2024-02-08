10215 KO no default tentando update primeiro

Indice em realizado_em ?
FOR UPDATE seria mais rapido ? sim
Testar outros levels de isolation 
Repeatable Read => pior que SOL01 7108 KO
SSI => Pior de todos ate agora 12348 KO

SOL01 => 5956 KO com o select for update !

SOL02 => Lock advisory no inicio => 10k KO, como assim!

SOL03 => inserte da transacao antes do lock e do update do cliente ! KO=9202

08 de fevereiro

hoje vou tentar jogar a logica do saldo para o banco

SOL04 => 3600 KO melhor ate agora, eu usei um if < 5 pra validar se o cliente existe ou não kkk

Agora vamos pegar sério: procedures

SOL05 => 2800 KO Procedure

Vou melhorar o extrato tambem, mas ...

Vou tentar mecher nas configurações para limitar as requests

