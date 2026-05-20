import socket
import struct
import threading
import time
import horta_pb2

# ==========================================
# CONFIGURAÇÕES DA REDE E TIMERS
# ==========================================
GRUPO_MULTICAST = '224.1.1.1'
PORTA_MULTICAST = 5000
PORTA_DADOS_UDP = 5005
PORTA_TCP_CLIENTE = 5007

# Dicionários e Memória (com seus respectivos Locks para Thread-Safety)
fontes_ativas = {}
lock_fontes = threading.Lock()

historico_temperaturas = []
lock_historico = threading.Lock()

# ==========================================
# THREAD 1: BEACONING & DESCOBERTA (MULTICAST UDP)
# ==========================================
def gerenciar_descoberta():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2.0)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    ultimo_envio = 0
    print("[Descoberta] Serviço de Beaconing e Descoberta iniciado.")

    while True:
        agora = time.time()
        # Disparo a cada 4 segundos para resposta rápida
        if agora - ultimo_envio > 4:  
            try:
                sock.sendto(b"DISCOVER_HORTA", (GRUPO_MULTICAST, PORTA_MULTICAST))
                ultimo_envio = agora
            except Exception as e:
                print(f"[Erro Multicast] Falha ao enviar beacon: {e}")

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
# THREAD 2: TELEMETRIA CONTÍNUA (UDP)
# ==========================================
def receber_telemetria_udp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Permite reutilizar a porta caso o processo anterior tenha crashado
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORTA_DADOS_UDP))
    
    print(f"[Telemetria] Escutando dados contínuos via UDP na porta {PORTA_DADOS_UDP}...")

    while True:
        try:
            dados, addr = sock.recvfrom(1024)
            leitura = horta_pb2.LeituraClima()
            leitura.ParseFromString(dados)
            
            chave_sensor = f"{addr[0]}:5005" 
            with lock_fontes:
                if chave_sensor in fontes_ativas:
                    fontes_ativas[chave_sensor]["ultimo_visto"] = time.time()
            
            # Salva o histórico de temperatura
            with lock_historico:
                historico_temperaturas.append(leitura.temperatura)
                if len(historico_temperaturas) > 100:
                    historico_temperaturas.pop(0)
            
            print(f"[Dados] {leitura.id_sensor} -> Temp: {leitura.temperatura}°C | Umid: {leitura.umidade}%")
            
        except Exception as e:
            print(f"[Erro Telemetria] Falha ao receber pacote UDP: {e}")

# ==========================================
# FUNÇÃO AUXILIAR: LIMPEZA DINÂMICA
# ==========================================
def obter_lista_limpa():
    agora = time.time()
    dispositivos_vivos = []
    chaves_mortas = []
    
    with lock_fontes:
        for chave, dados in fontes_ativas.items():
            if agora - dados["ultimo_visto"] > 10.0:  # Tolerância reduzida para 10 segundos
                chaves_mortas.append(chave)
            else:
                dispositivos_vivos.append(dados["info"])
                
        for chave in chaves_mortas:
            print(f"\n[-] Fonte desconectada por inatividade: {chave}")
            del fontes_ativas[chave]
            
    return dispositivos_vivos

# ==========================================
# THREAD PRINCIPAL: SERVIDOR TCP
# ==========================================
def executar_gateway():
    print("=" * 50)
    print("🌾 INICIALIZANDO GATEWAY CENTRAL - SMART HORTA 🌾")
    print("=" * 50)

    t_descoberta = threading.Thread(target=gerenciar_descoberta, daemon=True)
    t_telemetria = threading.Thread(target=receber_telemetria_udp, daemon=True)
    
    t_descoberta.start()
    t_telemetria.start()
    
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
                
                tipo_alvo = "lampada_uv" if "luz" in requisicao.acao_comando else "valvula_irrigacao"
                print(f"\n[Comando TCP] Recebido do Cliente: Alvo ID='{requisicao.id_alvo}' | Ação='{requisicao.acao_comando}'")
                
                with lock_fontes:
                    for dados in fontes_ativas.values():
                        if dados["info"].tipo == tipo_alvo:
                            alvo_ip = dados["info"].ip
                            alvo_porta = dados["info"].porta
                            break 
                
                if alvo_ip and alvo_porta:
                    try:
                        print(f"[Roteamento] Conectando a {tipo_alvo.upper()} em {alvo_ip}:{alvo_porta}...")
                        
                        sock_alvo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock_alvo.settimeout(3.0)
                        sock_alvo.connect((alvo_ip, alvo_porta))
                        
                        comando_out = horta_pb2.ComandoRequisicao()
                        comando_out.id_alvo = requisicao.id_alvo
                        comando_out.acao = requisicao.acao_comando
                        
                        sock_alvo.sendall(comando_out.SerializeToString())
                        
                        # A CHAVE MÁGICA: Destrava a leitura do Java informando o fim do envio
                        sock_alvo.shutdown(socket.SHUT_WR)
                        
                        dados_resp = sock_alvo.recv(1024)
                        
                        resp_alvo = horta_pb2.ComandoResposta()
                        resp_alvo.ParseFromString(dados_resp)
                        
                        status_log = "Sucesso" if resp_alvo.sucesso else "Falha"
                        print(f"[Roteamento] Retorno de {tipo_alvo.upper()}: [{status_log}] {resp_alvo.mensagem}")
                        
                        resposta.sucesso = resp_alvo.sucesso
                        resposta.payload_texto = f"Retorno de {tipo_alvo.upper()}: {resp_alvo.mensagem}"
                        
                        sock_alvo.close()
                    except Exception as e:
                        print(f"[Erro Roteamento] Falha ao falar com {tipo_alvo.upper()}: {e}")
                        resposta.sucesso = False
                        resposta.payload_texto = f"Erro de rede ao repassar comando para {tipo_alvo.upper()}: {e}"
                else:
                    print(f"[Aviso] Comando ignorado. Dispositivo do tipo '{tipo_alvo.upper()}' não está online.")
                    resposta.sucesso = False
                    resposta.payload_texto = f"Comando falhou: Nenhum equipamento do tipo '{tipo_alvo.upper()}' online no momento."
            else:
                resposta.sucesso = False
                resposta.payload_texto = "Operação desconhecida pelo Gateway Central."
                
            conexao.sendall(resposta.SerializeToString())
            conexao.close()
            
        except Exception as e:
            print(f"[Erro Servidor TCP] Falha na comunicação com o Cliente: {e}")

if __name__ == "__main__":
    executar_gateway()