import socket
import struct
import time
import random
import threading
import horta_pb2

# ==========================================
# CONFIGURAÇÕES
# ==========================================
GRUPO_MULTICAST = '224.1.1.1'
PORTA_MULTICAST = 5000
PORTA_DADOS_GATEWAY = 5005

gateway_ip = None

def escutar_multicast():
    """Thread 1: Ouve eternamente os beacons do Gateway e responde."""
    global gateway_ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORTA_MULTICAST))
    
    mreq = struct.pack("4sl", socket.inet_aton(GRUPO_MULTICAST), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"[Descoberta] Sensor ouvindo multicast em {PORTA_MULTICAST}...")

    while True:
        dados_recebidos, endereco_gateway = sock.recvfrom(1024)
        if dados_recebidos == b"DISCOVER_HORTA":
            gateway_ip = endereco_gateway[0] # Atualiza o IP alvo
            
            resposta = horta_pb2.DiscoveryInfo()
            resposta.tipo = "sensor_clima"
            resposta.ip = "127.0.0.1"
            resposta.porta = PORTA_DADOS_GATEWAY 
            resposta.estado_inicial = "ativo"

            sock.sendto(resposta.SerializeToString(), endereco_gateway)

def enviar_telemetria():
    """Thread 2: Envia os dados de clima via UDP a cada 5s."""
    global gateway_ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print("[Telemetria] Aguardando descobrir o Gateway para enviar dados...")

    while True:
        if gateway_ip: # Só envia se já sabe quem é o Gateway
            leitura = horta_pb2.LeituraClima()
            leitura.id_sensor = "estufa_norte_1"
            leitura.temperatura = round(random.uniform(22.0, 30.0), 2)
            leitura.umidade = round(random.uniform(50.0, 70.0), 2)
            leitura.timestamp = int(time.time())

            sock.sendto(leitura.SerializeToString(), (gateway_ip, PORTA_DADOS_GATEWAY))
            print(f"[Enviado] Temp: {leitura.temperatura}°C | Umid: {leitura.umidade}%")
            
        time.sleep(2)

if __name__ == "__main__":
    t_multicast = threading.Thread(target=escutar_multicast, daemon=True)
    t_telemetria = threading.Thread(target=enviar_telemetria, daemon=True)
    
    t_multicast.start()
    t_telemetria.start()
    
    # Mantém o script principal rodando
    while True:
        time.sleep(1)