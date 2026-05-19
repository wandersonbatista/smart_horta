import socket
import struct
import threading
import time
import horta_pb2

# ==========================================
# CONFIGURAÇÕES
# ==========================================
GRUPO_MULTICAST = '224.1.1.1'
PORTA_MULTICAST = 5000
MINHA_PORTA_TCP = 5006

estado_valvula = "desligado"

def escutar_multicast():
    """Thread 1: Mantém a Válvula viva no Gateway respondendo aos beacons."""
    global estado_valvula
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORTA_MULTICAST))
    
    mreq = struct.pack("4sl", socket.inet_aton(GRUPO_MULTICAST), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"[Descoberta] Válvula ouvindo multicast em {PORTA_MULTICAST}...")

    while True:
        dados_recebidos, endereco_gateway = sock.recvfrom(1024)
        if dados_recebidos == b"DISCOVER_HORTA":
            resposta = horta_pb2.DiscoveryInfo()
            resposta.tipo = "valvula_irrigacao"
            resposta.ip = "127.0.0.1"
            resposta.porta = MINHA_PORTA_TCP
            resposta.estado_inicial = estado_valvula # Reporta o estado real atual

            sock.sendto(resposta.SerializeToString(), endereco_gateway)

def servidor_tcp():
    """Thread 2: Escuta e executa comandos do Gateway Central."""
    global estado_valvula
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_tcp.bind(('', MINHA_PORTA_TCP))
    sock_tcp.listen(1)
    
    print(f"[Servidor TCP] Válvula pronta para comandos na porta {MINHA_PORTA_TCP}...")

    while True:
        conexao, endereco = sock_tcp.accept()
        try:
            dados = conexao.recv(1024)
            if not dados: continue
            
            comando = horta_pb2.ComandoRequisicao()
            comando.ParseFromString(dados)
            print(f"\n[Comando Recebido] Ação: {comando.acao}")
            
            resposta = horta_pb2.ComandoResposta()
            
            if comando.acao == "ativar_bomba":
                estado_valvula = "ligado"
                resposta.sucesso = True
                resposta.mensagem = "Bomba de irrigação ativada!"
            elif comando.acao == "desativar_bomba":
                estado_valvula = "desligado"
                resposta.sucesso = True
                resposta.mensagem = "Bomba de irrigação desativada!"
            else:
                resposta.sucesso = False
                resposta.mensagem = f"Comando '{comando.acao}' inválido."
                
            conexao.sendall(resposta.SerializeToString())
            print(f"-> Estado alterado para: {estado_valvula.upper()}")
            
        finally:
            conexao.close()

if __name__ == "__main__":
    t_multicast = threading.Thread(target=escutar_multicast, daemon=True)
    t_tcp = threading.Thread(target=servidor_tcp, daemon=True)
    
    t_multicast.start()
    t_tcp.start()
    
    while True:
        time.sleep(1)