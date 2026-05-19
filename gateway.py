import socket
import struct
import horta_pb2

# Configurações
GRUPO_MULTICAST = '224.1.1.1'
PORTA_MULTICAST = 5000
MINHA_PORTA_DADOS = 5005

def executar_gateway():
    # --- FASE 1: DESCOBERTA ---
    sock_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock_multicast.settimeout(5.0) 
    ttl = struct.pack('b', 1)
    sock_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    print(f"Gateway: Enviando requisição de descoberta...")
    sock_multicast.sendto(b"DISCOVER_HORTA", (GRUPO_MULTICAST, PORTA_MULTICAST))

    fontes_ativas = []

    while True:
        try:
            dados_bytes, endereco_sensor = sock_multicast.recvfrom(1024)
            info = horta_pb2.DiscoveryInfo()
            info.ParseFromString(dados_bytes)
            
            print(f"Nova fonte descoberta: {info.tipo} em {endereco_sensor}")
            fontes_ativas.append(info)
        except socket.timeout:
            print(f"Fim da descoberta. {len(fontes_ativas)} dispositivo(s) encontrado(s).")
            sock_multicast.close()
            break

    # --- FASE 2: RECEPÇÃO DE LEITURAS (TELEMETRIA) ---
    print(f"\nGateway escutando dados contínuos na porta {MINHA_PORTA_DADOS}...")
    sock_dados = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_dados.bind(('', MINHA_PORTA_DADOS))

    while True:
        dados_bytes, endereco_fonte = sock_dados.recvfrom(1024)
        
        leitura_recebida = horta_pb2.LeituraClima()
        leitura_recebida.ParseFromString(dados_bytes)
        
        print(f"Recebido de {leitura_recebida.id_sensor} ({endereco_fonte[0]}): "
              f"Temp: {leitura_recebida.temperatura}°C | Umid: {leitura_recebida.umidade}%")

if __name__ == "__main__":
    executar_gateway()