import socket
import sys
import horta_pb2

GATEWAY_IP = "127.0.0.1"
GATEWAY_PORTA_CLIENTE = 5007  # Porta TCP exclusiva para o Cliente Analítico

def enviar_requisicao(requisicao):
    # Estabelece uma conexão TCP a cada comando disparado
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.connect((GATEWAY_IP, GATEWAY_PORTA_CLIENTE))
        
        # Serializa e envia via TCP
        sock_tcp.sendall(requisicao.SerializeToString())
        
        # Aguarda a resposta processada do Gateway (buffer de 4KB)
        dados_resposta = sock_tcp.recv(4096)
        resposta = horta_pb2.RespostaCliente()
        resposta.ParseFromString(dados_resposta)
        
        sock_tcp.close()
        return resposta
        
    except ConnectionRefusedError:
        return None

def menu():
    while True:
        print("\n" + "="*45)
        print("🌾 PAINEL DO AGRICULTOR - HORTA INTELIGENTE 🌾")
        print("="*45)
        print("1. Listar fontes conectadas e seus estados")
        print("2. Consultar média de temperatura (Agregada)")
        print("3. Ativar Válvula de Irrigação")
        print("4. Desativar Válvula de Irrigação")
        print("0. Sair")
        
        opcao = input("\nEscolha uma operação: ")
        
        requisicao = horta_pb2.RequisicaoCliente()
        
        # Mapeia as opções para os comandos do Protocol Buffers
        if opcao == "1":
            requisicao.operacao = "listar_fontes"
        elif opcao == "2":
            requisicao.operacao = "consultar_media_temp"
        elif opcao == "3":
            requisicao.operacao = "enviar_comando"
            requisicao.id_alvo = "valvula_01"  
            requisicao.acao_comando = "ativar_bomba"
        elif opcao == "4":
            requisicao.operacao = "enviar_comando"
            requisicao.id_alvo = "valvula_01"
            requisicao.acao_comando = "desativar_bomba"
        elif opcao == "0":
            print("Encerrando cliente...")
            sys.exit(0)
        else:
            print("Opção inválida.")
            continue

        # Processa o envio e aguarda o Gateway
        print("\nComunicando com o Gateway central...")
        resposta = enviar_requisicao(requisicao)
        
        if resposta:
            status = "✅ OK" if resposta.sucesso else "❌ ERRO"
            print(f"\n[{status}] Resultado:")
            print(resposta.payload_texto)
        else:
            print("\n❌ ERRO: Não foi possível conectar ao Gateway. Verifique se ele está no ar.")

if __name__ == "__main__":
    menu()