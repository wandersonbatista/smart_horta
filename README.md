<div style="text-align: justify;">

# 🌾SmartHorta - Sistemas Distribuídos

Equipe:<br>
 - ISRAEL DA SILVA FERNANDES - 538891 <br>
 - MATEUS DE JESUS VENANCIO DE SOUZA - 535979 <br>
 - WANDESON PAULINO BATISTA - 475663 <br> 

<br> 

# 📖 Apresentação do Projeto

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Este projeto implementa um sistema distribuído robusto para o monitoramento e controle de uma Horta Inteligente. O objetivo do sistema é consolidar conceitos fundamentais de redes e sistemas distribuídos, como comunicação via sockets (TCP e UDP), serialização padronizada de dados com Protocol Buffers, concorrência por meio de múltiplas Threads e descoberta dinâmica de serviços em rede local usando Multicast.

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Para demonstrar a interoperabilidade entre diferentes tecnologias, o ecossistema foi construído de forma poliglota, distribuindo as responsabilidades em processos completamente isolados:

- Gateway Inteligente (Python): O nó central da rede. Ele opera de forma assíncrona gerenciando três tarefas simultâneas: envia beacons de descoberta por Multicast, recebe telemetria contínua via pacotes UDP e mantém um servidor TCP para atender às requisições do painel do usuário e rotear comandos para os atuadores.

* Fontes de Dados (Sensores e Atuadores): 

     - Sensor de Clima (Python): Dispositivo que monitora o ambiente disparando leituras contínuas de temperatura e umidade via UDP.

     - Válvula de Irrigação (Python): Atuador controlado que abre um servidor TCP próprio para receber comandos de ativação/desativação do fluxo de água.

     - Lâmpada UV de Crescimento (Java): Componente poliglota do sistema. Escuta os anúncios de rede do Gateway e abre um servidor TCP em ambiente Java para ligar/desligar a iluminação artificial.

     - Cliente Analítico (Python): Interface em linha de comando que funciona como o painel de controle do agricultor. Ele conecta-se via TCP ao Gateway para listar os dispositivos online, calcular métricas agregadas e disparar ações na estufa.

# ⚙️ Requisitos do Sistema

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Para configurar o ambiente, compilar os contratos de comunicação e executar os nós da rede, os seguintes requisitos são necessários:

- Python 3.x

- Java Development Kit (JDK 11 ou superior)

- Protocol Buffers Compiler (protoc)

     - Instalação no Linux: 
     
                sudo apt install protobuf-compiler
     - Instalação no Windows:

                winget install protobuf

     - MacOS:

                brew install protobuf

- Biblioteca Protobuf para Java: Arquivo binário protobuf-java-3.21.12.jar (ou versão equivalente ao seu compilador protoc) inserido na raiz do projeto.

<br>

# 🧑‍💻 Instalação das dependências
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

    &ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Com o ambiente virtual ativado, compile o arquivo de definição de mensagens para gerar o suporte ao Python e Java:
    Bash

     - Compilar suporte para Python:

                protoc -I=. --python_out=. horta.proto

     - Compilar suporte para Java
                
                protoc -I=. --java_out=. horta.proto

    &ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Isso gerará o arquivo _horta_pb2.py_ e criará o pacote interno estruturado em _smart_horta/Horta.java_ responsável pela serialização dos dados.

6. Compilação do Componente Java (Lâmpada UV): 
                
    &ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Ainda na raiz do projeto, compile a classe da Lâmpada UV vinculando a biblioteca .jar ao Classpath: 
        
        javac -cp "protobuf-java-3.21.12.jar:." LampadaUV.java smart_horta/Horta.java
<br>

# 🚀 Como Executar  

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;Para simular a concorrência e o isolamento real, execute cada comando abaixo em uma janela ou aba independente do seu terminal, garantindo que o ambiente virtual Python esteja ativo nas abas referentes ao Python.

- Válvula de Irrigação (Python):

        Bash:
                python3 valvula.py

- Sensor de Clima (Python):
        
        Bash:
                python3 sensor.py

- Lâmpada UV (Java):

        Bash:

                java -cp "protobuf-java-3.21.12.jar:." LampadaUV

- Gateway Central (Python):

        Bash:
                python3 gateway.py

- Cliente Analítico (Python):
        
        Bash:
                python3 client.py

</div>
