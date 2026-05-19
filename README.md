# smart_horta
Traballho da disciplina de Sistemas Distribuídos

📖 Apresentação do Projeto

Este projeto implementa um sistema distribuído que simula o monitoramento e controle de uma Horta Inteligente. O sistema visa consolidar conceitos de comunicação entre processos utilizando sockets TCP e UDP , serialização de mensagens com Protocol Buffers e descoberta de dispositivos na rede utilizando multicast.  

O projeto adapta a proposta arquitetural de uma "cidade inteligente"  para o contexto agrícola, sendo composto por três grandes componentes que operam de forma isolada:  

    Gateway Inteligente: Atua como o nó central do sistema para coleta, agregação e monitoramento. Ele gerencia o estado das fontes via TCP , realiza a descoberta inicial via multicast UDP e recebe continuamente a telemetria dos sensores via pacotes UDP.  

Fontes de Dados (Sensores e Atuadores): Processos independentes que representam os equipamentos da estufa. Elas escutam e participam da fase de descoberta via multicast UDP.  

    Sensores Contínuos (ex: Clima): Enviam leituras (temperatura e umidade) de tempos em tempos ao Gateway via UDP.  

Fontes Controláveis (ex: Válvula de Irrigação): Recebem comandos do Gateway via conexões TCP para alterar parâmetros de operação ou simular falhas.  

Cliente Analítico: Um processo separado que se conecta ao Gateway via TCP. Ele fornece uma interface para que o usuário consulte as fontes ativas, visualize estados operacionais e envie comandos de controle para a horta.  

Toda a comunicação, independentemente do protocolo de transporte (TCP ou UDP), tem suas mensagens serializadas rigorosamente através do Protocol Buffers.  

⚙️ Requisitos do Sistema

Para configurar o ambiente, compilar os contratos de comunicação e executar os nós da rede, os seguintes requisitos são necessários:

    Python 3.x: Linguagem escolhida para a implementação da lógica de rede, sockets e processos.

    Protocol Buffers Compiler (protoc): O compilador oficial necessário para gerar as classes nativas a partir do nosso contrato de dados (.proto).

        Debian/Ubuntu/Kali: sudo apt install protobuf-compiler

    Biblioteca Protobuf para Python: Pacote necessário para instanciar as mensagens no código.

        Instalação: pip install protobuf

    Ambiente de Rede Local: O sistema operacional deve suportar binding de portas locais e roteamento multicast habilitado (funcionalidade padrão na maioria dos ambientes Linux e Windows locais).

🚀 Como Executar
1. Configuração do Ambiente Virtual (venv)

Na raiz do projeto, execute os comandos abaixo para criar e ativar o ambiente isolado, e em seguida instalar a biblioteca do Protocol Buffers:
Bash

# 1. Criar o ambiente virtual chamado 'venv'
python3 -m venv venv

# 2. Ativar o ambiente virtual
# No Linux/macOS:
source venv/bin/activate
# No Windows (Prompt de Comando):
venv\Scripts\activate
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# 3. Instalar a biblioteca do Protobuf no ambiente isolado
pip install protobuf

(Nota: Sempre que abrir um novo terminal para rodar um componente, lembre-se de ativar o ambiente virtual com o comando source venv/bin/activate antes de prosseguir).
2. Compilação do Contrato (Protobuf)

Com o ambiente virtual ativado, compile o arquivo de definição de mensagens para gerar o suporte ao Python:
Bash

protoc -I=. --python_out=. horta.proto

Isso gerará o arquivo horta_pb2.py, responsável pela serialização dos dados.
3. Inicialização do Sistema Distribuído

A execução exige que cada componente seja levantado em um processo isolado (terminais separados) para garantir a simulação correta de concorrência. Certifique-se de ativar o ambiente virtual em cada nova janela de terminal utilizada.  

    Levante as Fontes de Dados:
    Inicie a válvula de irrigação e o sensor de clima. Eles ficarão em estado de "escuta", aguardando a chamada multicast.  

Bash

python valvula.py
python sensor.py

Inicie o Gateway Central:
No terceiro terminal, execute o gateway. Ele fará o disparo multicast, registrará as fontes descobertas em até 5 segundos e, logo após, abrirá as portas para escutar as leituras UDP e conexões TCP.  

Bash

python gateway.py

Execute o Cliente Analítico:
No quarto terminal, levante a interface do usuário. Através deste painel interativo, você poderá listar os equipamentos e enviar requisições TCP para o Gateway atuar na estufa.  

Bash

    python cliente.py