import os
import time
import win32api
import win32print

# --- CONFIGURAÇÃO ---
PASTA_FILA = "fila_impressao"
PASTA_IMPRESSOS = "pedidos_impressos"

# Cria a pasta de backup se não existir
if not os.path.exists(PASTA_IMPRESSOS):
    os.makedirs(PASTA_IMPRESSOS)

print(f"--- INICIANDO O VIGIA DE IMPRESSÃO ---")
print(f"Vigiando a pasta: {PASTA_FILA}")
print("Pressione Ctrl+C para parar.")

def imprimir_arquivo(caminho_arquivo):
    """
    Manda um arquivo de texto para a impressora padrão do Windows.
    """
    try:
        # Pega o nome da impressora padrão do Windows
        impressora_padrao = win32print.GetDefaultPrinter()
        print(f"Tentando imprimir na: {impressora_padrao}...")
        
        # Manda imprimir usando o comando nativo do Windows
        # O comando '/p' diz ao bloco de notas para imprimir e fechar
        win32api.ShellExecute(0, "print", caminho_arquivo, f'/d:"{impressora_padrao}"', ".", 0)
        
        return True
    except Exception as e:
        print(f"!!! Erro ao imprimir: {e}")
        return False

while True:
    try:
        # Lista todos os arquivos na pasta
        arquivos = os.listdir(PASTA_FILA)
        
        for nome_arquivo in arquivos:
            if nome_arquivo.endswith(".txt"):
                caminho_completo = os.path.join(PASTA_FILA, nome_arquivo)
                
                print(f">>> Novo pedido encontrado: {nome_arquivo}")
                
                # Tenta imprimir
                sucesso = imprimir_arquivo(caminho_arquivo=caminho_completo)
                
                if sucesso:
                    # Se imprimiu, move para a pasta de "já impressos"
                    # Espera 2 segundos para garantir que o Windows liberou o arquivo
                    time.sleep(2) 
                    destino = os.path.join(PASTA_IMPRESSOS, nome_arquivo)
                    
                    # Se já existir um arquivo com mesmo nome no destino, remove antes
                    if os.path.exists(destino):
                        os.remove(destino)
                        
                    os.rename(caminho_completo, destino)
                    print(f">>> Arquivo movido para {PASTA_IMPRESSOS}")
                    print("-" * 30)
        
        # Espera 2 segundos antes de olhar a pasta de novo
        time.sleep(2)
        
    except Exception as e:
        print(f"Erro no loop principal: {e}")
        time.sleep(5)