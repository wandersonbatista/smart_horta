import socket
import struct
import time
import random
import horta_pb2

# Configurações do Multicast e Dados
GRUPO_MULTICAST = '224.1.1.1'
PORTA_MULTICAST = 5000
PORTA_DADOS_GATEWAY = 5005

def executar_sensor():
    # --- FASE 1: DESCOBERTA ---
    sock_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_multicast.bind(('', PORTA_MULTICAST))
    
    mreq = struct.pack("4sl", socket.inet_aton(GRUPO_MULTICAST), socket.INADDR_ANY)
    sock_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Sensor (Estufa Norte) escutando multicast na porta {PORTA_MULTICAST}...")
    
    gateway_ip = None

    # Fica aguardando a mensagem de descoberta do Gateway
    while True:
        dados_recebidos, endereco_gateway = sock_multicast.recvfrom(1024)
        if dados_recebidos == b"DISCOVER_HORTA":
            print(f"\nRequisição recebida de {endereco_gateway}. Respondendo...")
            
            resposta = horta_pb2.DiscoveryInfo()
            resposta.tipo = "sensor_clima"
            resposta.ip = "127.0.0.1" 
            resposta.porta = PORTA_DADOS_GATEWAY 
            resposta.estado_inicial = "ativo"

            sock_multicast.sendto(resposta.SerializeToString(), endereco_gateway)
            print("Resposta enviada! Encerrando fase de descoberta.")
            
            # Salva o IP do gateway para enviar os dados depois e sai do loop
            gateway_ip = endereco_gateway[0]
            sock_multicast.close()
            break 

    # --- FASE 2: ENVIO DE LEITURAS (TELEMETRIA) ---
    print(f"\nIniciando envio contínuo de leituras para o Gateway em {gateway_ip}:{PORTA_DADOS_GATEWAY}...")
    sock_dados = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        leitura = horta_pb2.LeituraClima()
        leitura.id_sensor = "estufa_norte_1"
        leitura.temperatura = round(random.uniform(22.0, 30.0), 2)
        leitura.umidade = round(random.uniform(50.0, 70.0), 2)
        leitura.timestamp = int(time.time())

        sock_dados.sendto(leitura.SerializeToString(), (gateway_ip, PORTA_DADOS_GATEWAY))
        print(f"Enviado: Temp {leitura.temperatura}°C | Umid {leitura.umidade}%")
        
        time.sleep(5) # Envia a cada 5 segundos

if __name__ == "__main__":
    executar_sensor()