import socket
import struct
import threading
import time
import horta_pb2

# ==========================================
# CONFIGURAÇÕES DA REDE
# ==========================================
GRUPO_MULTICAST = '224.1.1.1'
PORTA_MULTICAST = 5000
PORTA_DADOS_UDP = 5005
PORTA_TCP_CLIENTE = 5007

# Dicionário global para armazenar o estado das fontes descobertas
# Chave: "IP:Porta", Valor: {"info": DiscoveryInfo, "ultimo_visto": float}
fontes_ativas = {}
lock_fontes = threading.Lock()
historico_temperaturas = []
lock_historico = threading.Lock()

# ==========================================
# THREAD 1: BEACONING & DESCOBERTA (MULTICAST UDP)
# ==========================================
def gerenciar_descoberta():
    """
    Envia beacons multicast a cada 10s e escuta as respostas das fontes.
    Garante a conexão dinâmica independente da ordem de inicialização.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2.0) # Timeout curto para permitir que o loop verifique o tempo de envio
    
    # Configura o TTL para 1 (rede local)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    ultimo_envio = 0
    print("[Descoberta] Serviço de Beaconing e Descoberta iniciado.")

    while True:
        agora = time.time()
        
        # Dispara o gatilho em multicast a cada 10 segundos
        if agora - ultimo_envio > 4:
            try:
                sock.sendto(b"DISCOVER_HORTA", (GRUPO_MULTICAST, PORTA_MULTICAST))
                ultimo_envio = agora
            except Exception as e:
                print(f"[Erro Multicast] Falha ao enviar beacon: {e}")

        # Tenta ouvir respostas Unicast das fontes de dados
        try:
            dados, endereco = sock.recvfrom(1024)
            info = horta_pb2.DiscoveryInfo()
            info.ParseFromString(dados)
            
            chave = f"{info.ip}:{info.porta}"
            
            with lock_fontes:
                novo_dispositivo = chave not in fontes_ativas
                fontes_ativas[chave] = {
                    "info": info,
                    "ultimo_visto": time.time()
                }
            
            if novo_dispositivo:
                print(f"\n[+] Nova fonte registrada: {info.tipo.upper()} em {chave} (Estado: {info.estado_inicial})")
                
        except socket.timeout:
            pass
        except Exception as e:
            print(f"[Erro Descoberta] Falha ao processar resposta: {e}")

# ==========================================
# THREAD 2: TELEMETRIA CONTINUA (UDP)
# ==========================================
def receber_telemetria_udp():
    """
    Escuta ininterruptamente as leituras de clima enviadas via pacotes UDP.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', PORTA_DADOS_UDP))
    
    print(f"[Telemetria] Escutando dados contínuos via UDP na porta {PORTA_DADOS_UDP}...")

    while True:
        try:
            dados, addr = sock.recvfrom(1024)
            leitura = horta_pb2.LeituraClima()
            leitura.ParseFromString(dados)
            
            # Atualiza o timestamp "ultimo_visto" usando o IP de origem
            # (Substitua o trecho equivalente dentro do while True da telemetria)
            chave_sensor = f"{addr[0]}:5005" 
            with lock_fontes:
                if chave_sensor in fontes_ativas:
                    fontes_ativas[chave_sensor]["ultimo_visto"] = time.time()
            
            # --- NOVO CÓDIGO: Salva o histórico ---
            with lock_historico:
                historico_temperaturas.append(leitura.temperatura)
                # Mantém apenas as últimas 100 leituras para não estourar a memória
                if len(historico_temperaturas) > 100:
                    historico_temperaturas.pop(0)
            # --------------------------------------

            print(f"[Dados] {leitura.id_sensor} -> Temp: {leitura.temperatura}°C | Umid: {leitura.umidade}%")

        except Exception as e:
            print(f"[Erro Telemetria] Falha ao receber pacote UDP: {e}")

# ==========================================
# FUNÇÃO AUXILIAR: LIMPEZA DINÂMICA DE FONTES (HEARTBEAT)
# ==========================================
def obter_lista_limpa():
    """
    Varre o dicionário e remove quem está offline há mais de 20 segundos.
    Retorna uma lista limpa com objetos DiscoveryInfo atualizados.
    """
    agora = time.time()
    dispositivos_vivos = []
    chaves_mortas = []
    
    with lock_fontes:
        for chave, dados in fontes_ativas.items():
            # Se passou de 20 segundos sem sinal de vida, consideramos desconectado
            if agora - dados["ultimo_visto"] > 10.0:
                chaves_mortas.append(chave)
            else:
                dispositivos_vivos.append(dados["info"])
                
        # Remove fisicamente as fontes inativas do dicionário
        for chave in chaves_mortas:
            print(f"\n[-] Fonte desconectada por inatividade: {chave}")
            del fontes_ativas[chave]
            
    return dispositivos_vivos

# ==========================================
# THREAD PRINCIPAL: SERVIDOR TCP (INTERACTION COM CLIENTE)
# ==========================================
def executar_gateway():
    print("=" * 50)
    print("🌾 INICIALIZANDO GATEWAY CENTRAL - SMART HORTA 🌾")
    print("=" * 50)

    # Inicializa as threads auxiliares em background
    t_descoberta = threading.Thread(target=gerenciar_descoberta, daemon=True)
    t_telemetria = threading.Thread(target=receber_telemetria_udp, daemon=True)
    
    t_descoberta.start()
    t_telemetria.start()
    
    # Configuração do Servidor TCP para o Cliente Analítico
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_tcp.bind(('', PORTA_TCP_CLIENTE))
    sock_tcp.listen(5)
    
    print(f"[Servidor TCP] Escutando Cliente Analítico na porta {PORTA_TCP_CLIENTE}...\n")
    
    while True:
        try:
            conexao, endereco_cliente = sock_tcp.accept()
            
            dados_bytes = conexao.recv(4096)
            if not dados_bytes:
                conexao.close()
                continue
                
            requisicao = horta_pb2.RequisicaoCliente()
            requisicao.ParseFromString(dados_bytes)
            
            resposta = horta_pb2.RespostaCliente()
            
            # --- PROCESSAMENTO DOS COMANDOS ---
            if requisicao.operacao == "listar_fontes":
                dispositivos_vivos = obter_lista_limpa()
                
                if not dispositivos_vivos:
                    resposta.payload_texto = "Nenhuma fonte de dados conectada no momento."
                else:
                    linhas = ["--- DISPOSITIVOS ONLINE ---"]
                    for d in dispositivos_vivos:
                        linhas.append(f" 🪴 {d.tipo.upper()} | IP/Porta: {d.ip}:{d.porta} | Estado: {d.estado_inicial}")
                    resposta.payload_texto = "\n".join(linhas)
                    
                resposta.sucesso = True
                
            elif requisicao.operacao == "consultar_media_temp":
                with lock_historico:
                    if not historico_temperaturas:
                        resposta.sucesso = False
                        resposta.payload_texto = "Aguardando dados: Nenhuma temperatura foi recebida ainda."
                    else:
                        media = sum(historico_temperaturas) / len(historico_temperaturas)
                        resposta.sucesso = True
                        resposta.payload_texto = f"📊 Média de Temperatura (últimas {len(historico_temperaturas)} leituras): {media:.2f}°C"
                
            elif requisicao.operacao == "enviar_comando":
                alvo_ip = None
                alvo_porta = None
                
                # 1. Busca a válvula na lista de fontes ativas
                with lock_fontes:
                    for dados in fontes_ativas.values():
                        if dados["info"].tipo == "valvula_irrigacao":
                            alvo_ip = dados["info"].ip
                            alvo_porta = dados["info"].porta
                            break # Encontrou a primeira válvula conectada
                
                # 2. Se a válvula estiver online, repassa o comando
                if alvo_ip and alvo_porta:
                    try:
                        # Abre conexão TCP direto com a válvula
                        sock_valvula = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock_valvula.settimeout(3.0)
                        sock_valvula.connect((alvo_ip, alvo_porta))
                        
                        # Monta o comando no formato Protobuf
                        comando_out = horta_pb2.ComandoRequisicao()
                        comando_out.id_alvo = requisicao.id_alvo
                        comando_out.acao = requisicao.acao_comando
                        
                        # Envia e aguarda a resposta
                        sock_valvula.sendall(comando_out.SerializeToString())
                        dados_resp = sock_valvula.recv(1024)
                        
                        resp_valvula = horta_pb2.ComandoResposta()
                        resp_valvula.ParseFromString(dados_resp)
                        
                        # Repassa o status e a mensagem da válvula para o Cliente
                        resposta.sucesso = resp_valvula.sucesso
                        resposta.payload_texto = f"Retorno da Válvula: {resp_valvula.mensagem}"
                        
                        sock_valvula.close()
                    except Exception as e:
                        resposta.sucesso = False
                        resposta.payload_texto = f"Erro de rede ao repassar comando para a válvula: {e}"
                else:
                    resposta.sucesso = False
                    resposta.payload_texto = "Comando falhou: Nenhuma válvula de irrigação online no momento."
                
            # Envia a resposta encapsulada via Protocol Buffers de volta ao cliente
            conexao.sendall(resposta.SerializeToString())
            conexao.close()
            
        except Exception as e:
            print(f"[Erro Servidor TCP] Falha na comunicação com o Cliente: {e}")

if __name__ == "__main__":
    executar_gateway()