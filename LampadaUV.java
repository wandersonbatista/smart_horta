import java.net.*;
import java.io.*;
import smart_horta.Horta; // Importação atualizada para o novo pacote
import smart_horta.Horta.ComandoRequisicao;
import smart_horta.Horta.ComandoResposta;
import smart_horta.Horta.DiscoveryInfo;
import smart_horta.Horta.ComandoResposta.Builder;

public class LampadaUV {
    // Configurações de Rede
    private static final String GRUPO_MULTICAST = "224.1.1.1";
    private static final int PORTA_MULTICAST = 5000;
    private static final int MINHA_PORTA_TCP = 5008; // Porta exclusiva para a Lâmpada UV
    
    private static String estadoLampada = "desligado";

    public static void main(String[] args) {
        System.out.println("☀️ Lâmpada UV (Java) Iniciada!");

        // --- THREAD 1: DESCOBERTA ---
        Thread threadMulticast = new Thread(() -> {
            try {
                InetAddress grupo = InetAddress.getByName(GRUPO_MULTICAST);
                MulticastSocket socket = new MulticastSocket(PORTA_MULTICAST);
                socket.joinGroup(grupo);
                
                System.out.println("[Descoberta] Ouvindo multicast...");
                byte[] buffer = new byte[1024];
                
                while (true) {
                    DatagramPacket pacoteRecebido = new DatagramPacket(buffer, buffer.length);
                    socket.receive(pacoteRecebido);
                    String mensagem = new String(pacoteRecebido.getData(), 0, pacoteRecebido.getLength());
                    
                    if (mensagem.equals("DISCOVER_HORTA")) {
                        // Constrói a mensagem usando o padrão Builder do Protobuf Java
                        Horta.DiscoveryInfo resposta = Horta.DiscoveryInfo.newBuilder()
                            .setTipo("lampada_uv")
                            .setIp("127.0.0.1")
                            .setPorta(MINHA_PORTA_TCP)
                            .setEstadoInicial(estadoLampada)
                            .build();
                            
                        byte[] dadosResposta = resposta.toByteArray();
                        DatagramPacket pacoteEnvio = new DatagramPacket(
                            dadosResposta, dadosResposta.length, 
                            pacoteRecebido.getAddress(), pacoteRecebido.getPort()
                        );
                        socket.send(pacoteEnvio);
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });

        // --- THREAD 2: COMANDOS ---
        Thread threadTcp = new Thread(() -> {
            try (ServerSocket serverSocket = new ServerSocket(MINHA_PORTA_TCP)) {
                System.out.println("[Servidor TCP] Lâmpada aguardando comandos na porta " + MINHA_PORTA_TCP + "...");
                
                while (true) {
                    Socket conexao = serverSocket.accept();
                    
                    // Lê os bytes recebidos e desserializa usando a classe atualizada
                    Horta.ComandoRequisicao comando = Horta.ComandoRequisicao.parseFrom(conexao.getInputStream());
                    System.out.println("\n[Comando Recebido] Ação: " + comando.getAcao());
                    
                    Horta.ComandoResposta.Builder respostaBuilder = Horta.ComandoResposta.newBuilder();
                    
                    if (comando.getAcao().equals("ligar_luz")) {
                        estadoLampada = "ligado";
                        respostaBuilder.setSucesso(true).setMensagem("Lâmpada UV Ativada com sucesso!");
                    } else if (comando.getAcao().equals("desligar_luz")) {
                        estadoLampada = "desligado";
                        respostaBuilder.setSucesso(true).setMensagem("Lâmpada UV Desativada com sucesso!");
                    } else {
                        respostaBuilder.setSucesso(false).setMensagem("Comando não reconhecido pela Lâmpada.");
                    }
                    
                    // Envia a resposta de volta e fecha a conexão
                    Horta.ComandoResposta resposta = respostaBuilder.build();
                    resposta.writeTo(conexao.getOutputStream());
                    conexao.close();
                    
                    System.out.println("-> Estado atual: " + estadoLampada.toUpperCase());
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });

        // Inicia as threads simultaneamente
        threadMulticast.start();
        threadTcp.start();
    }
}