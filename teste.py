import socket
import horta_pb2

VALVULA_IP = "127.0.0.1"
VALVULA_PORTA = 5006

# Cria o socket TCP como CLIENTE
sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print(f"Conectando à válvula em {VALVULA_IP}:{VALVULA_PORTA}...")
sock_tcp.connect((VALVULA_IP, VALVULA_PORTA))

# Monta o comando usando Protobuf
comando = horta_pb2.ComandoRequisicao()
comando.id_alvo = "valvula_01"
comando.acao = "desativar_bomba" # Tente mudar para "desativar_bomba" depois!

# Envia via TCP
print(f"Enviando comando '{comando.acao}'...")
sock_tcp.sendall(comando.SerializeToString())

# Aguarda a resposta (ComandoResposta)
dados_resposta = sock_tcp.recv(1024)
resposta = horta_pb2.ComandoResposta()
resposta.ParseFromString(dados_resposta)

print(f"\nResposta recebida da Válvula:")
print(f" - Sucesso: {resposta.sucesso}")
print(f" - Mensagem: {resposta.mensagem}")

sock_tcp.close()