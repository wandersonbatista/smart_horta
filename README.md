<div style="text-align: justify;">

# smart_horta
Traballho da disciplina de Sistemas Distribuídos

Equipe:<br>
 - ISRAEL DA SILVA FERNANDES - 538891 <br>
 - MATEUS DE JESUS VENANCIO DE SOUZA - 535979 <br>
 - WANDESON PAULINO BATISTA - 475663 <br> 
# 📖 Apresentação do Projeto

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Este projeto implementa um sistema distribuído 
que simula o monitoramento e controle de uma Horta Inteligente. O sistema visa consolidar conceitos de comunicação entre processos utilizando sockets TCP e UDP , serialização de mensagens com Protocol Buffers e descoberta de dispositivos na rede utilizando multicast.  

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;O projeto adapta a proposta arquitetural de uma "cidade inteligente"  para o contexto agrícola, sendo composto por três grandes componentes que operam de forma isolada:  

 - Gateway Inteligente: Atua como o nó central do sistema para coleta, agregação e monitoramento. Ele gerencia o estado das fontes via TCP , realiza a descoberta inicial via multicast UDP e recebe continuamente a telemetria dos sensores via pacotes UDP.  

 - Fontes de Dados (Sensores e Atuadores): Processos independentes que representam os equipamentos da estufa. Elas escutam e participam da fase de descoberta via multicast UDP.  

 - Sensores Contínuos (ex: Clima): Enviam leituras (temperatura e umidade) de tempos em tempos ao Gateway via UDP.  

 - Fontes Controláveis (ex: Válvula de Irrigação): Recebem comandos do Gateway via conexões TCP para alterar parâmetros de operação ou simular falhas.  

 - Cliente Analítico: Um processo separado que se conecta ao Gateway via TCP. Ele fornece uma interface para que o usuário consulte as fontes ativas, visualize estados operacionais e envie comandos de controle para a horta.  

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Toda a comunicação, independentemente do protocolo de transporte (TCP ou UDP), tem suas mensagens serializadas rigorosamente através do Protocol Buffers.  

# ⚙️ Requisitos do Sistema

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Para configurar o ambiente, compilar os contratos de comunicação e executar os nós da rede, os seguintes requisitos são necessários:

- Python 3.x: Linguagem escolhida para a implementação da lógica de rede, sockets e processos.

- Protocol Buffers Compiler (protoc): O compilador oficial necessário para gerar as classes nativas a partir do nosso contrato de dados (.proto).

        - Linux(Debian): 
                sudo apt install protobuf-compiler
        
        - Windows:
                winget install protobuf
        
        - MacOS:
                brew install protobuf


- Biblioteca Protobuf para Python: Pacote necessário para instanciar as mensagens no código.

- Ambiente de Rede Local: O sistema operacional deve suportar binding de portas locais e roteamento multicast habilitado (funcionalidade padrão na maioria dos ambientes Linux e Windows locais).

<br>

# 🚀 Como Executar 
1. Configuração do Ambiente Virtual (venv)

    &ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Na raiz do projeto, execute os comandos abaixo para criar e ativar o ambiente isolado, e em seguida instalar a biblioteca do Protocol Buffers:
Bash

2. Criar o ambiente virtual:

        python3 -m venv venv

3. Ativar o ambiente virtual

        Linux/macOS:

                source venv/bin/activate

        Windows (PowerShell):

                .\venv\Scripts\Activate.ps1

4. Instalar a biblioteca do Protobuf no ambiente isolado

                pip install protobuf


5. Compilação do Contrato (Protobuf)

    &ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Com o ambiente virtual ativado, compile o arquivo de definição de mensagens para gerar o suporte ao Python:
    Bash

        protoc -I=. --python_out=. horta.proto

    &ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Isso gerará o arquivo horta_pb2.py, responsável pela serialização dos dados.
</div>
