import socket
import struct
import horta_pb2

# Configurações
GRUPO_MULTICAST = '224.1.1.1'
PORTA_MULTICAST = 5000
MINHA_PORTA_TCP = 5006  # Porta separada para receber os comandos

def executar_valvula():
    # --- FASE 1: DESCOBERTA (Ouvindo o Multicast) ---
    sock_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_multicast.bind(('', PORTA_MULTICAST))
    
    mreq = struct.pack("4sl", socket.inet_aton(GRUPO_MULTICAST), socket.INADDR_ANY)
    sock_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Válvula de Irrigação escutando multicast na porta {PORTA_MULTICAST}...")
    
    while True:
        dados_recebidos, endereco_gateway = sock_multicast.recvfrom(1024)
        if dados_recebidos == b"DISCOVER_HORTA":
            print(f"\nRequisição recebida. Respondendo para o Gateway...")
            
            resposta = horta_pb2.DiscoveryInfo()
            resposta.tipo = "valvula_irrigacao"
            resposta.ip = "127.0.0.1" 
            resposta.porta = MINHA_PORTA_TCP 
            resposta.estado_inicial = "desligado"

            sock_multicast.sendto(resposta.SerializeToString(), endereco_gateway)
            sock_multicast.close()
            break # Fim da descoberta

    # --- FASE 2: SERVIDOR TCP PARA RECEBER COMANDOS ---
    estado_valvula = "desligado"
    
    # Criando socket TCP (SOCK_STREAM)
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.bind(('', MINHA_PORTA_TCP))
    sock_tcp.listen(1) # Fica ouvindo (1 conexão concorrente por vez)
    
    print(f"\nVálvula pronta e aguardando comandos TCP na porta {MINHA_PORTA_TCP}...")
    
    while True:
        # Fica travado aqui até o Gateway conectar
        conexao, endereco_cliente = sock_tcp.accept()
        
        try:
            # 1. Recebe os bytes do comando TCP
            dados_bytes = conexao.recv(1024)
            if not dados_bytes:
                continue
                
            comando = horta_pb2.ComandoRequisicao()
            comando.ParseFromString(dados_bytes)
            
            print(f"\n[TCP] Comando recebido: Ação='{comando.acao}' | Alvo='{comando.id_alvo}'")
            
            # 2. Executa a lógica de controle e prepara a resposta
            resposta = horta_pb2.ComandoResposta()
            
            if comando.acao == "ativar_bomba":
                estado_valvula = "ligado"
                resposta.sucesso = True
                resposta.mensagem = "Bomba de irrigação ATIVADA com sucesso."
                
            elif comando.acao == "desativar_bomba":
                estado_valvula = "desligado"
                resposta.sucesso = True
                resposta.mensagem = "Bomba de irrigação DESATIVADA com sucesso."
                
            else:
                resposta.sucesso = False
                resposta.mensagem = f"Comando '{comando.acao}' não reconhecido."
            
            print(f"Estado atual da Válvula: {estado_valvula.upper()}")
            
            # 3. Envia a resposta de volta pelo mesmo túnel TCP
            conexao.sendall(resposta.SerializeToString())
            
        finally:
            # Encerra a conexão daquele comando específico e volta a escutar
            conexao.close()

if __name__ == "__main__":
    executar_valvula()