"""
Agente de Impressão Local - Dogão do Castelo
Este script roda no computador do balcão/cozinha do restaurante onde a impressora está conectada.
Ele consulta os novos pedidos na Nuvem e imprime diretamente na impressora térmica do Windows.
"""

import os
import sys
import time
import tempfile
import urllib.request
import urllib.error
import json

# Tentar importar win32print para impressão nativa no Windows
try:
    import win32api
    import win32print
    WIN32_DISPONIVEL = True
except ImportError:
    WIN32_DISPONIVEL = False

# --- Configurações do Agente ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Tentar carregar .env local se existir
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH)
    except Exception:
        pass

# URL do servidor (quando colocar na nuvem, troque por https://seu-dominio.com.br)
SERVER_URL = os.getenv('SERVER_URL', 'http://127.0.0.1:5000').rstrip('/')

# Token de autenticação (deve ser idêntico ao PRINTER_TOKEN do servidor)
PRINTER_TOKEN = os.getenv('PRINTER_TOKEN', 'dogao_printer_sec_9a8b7c6d5e4f3a2b1c0d')

INTERVALO_POLLING = 4  # segundos entre cada verificação

print("=" * 60)
print("     DOGÃO DO CASTELO - AGENTE DE IMPRESSÃO LOCAL")
print("=" * 60)
print(f"📡 Conectando ao Servidor: {SERVER_URL}")
print(f"⏱️  Intervalo de Verificação: {INTERVALO_POLLING}s")

if WIN32_DISPONIVEL:
    try:
        impressora_padrao = win32print.GetDefaultPrinter()
        print(f"🖨️  Impressora Padrão do Windows: {impressora_padrao}")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível obter a impressora padrão: {e}")
else:
    print("⚠️ Modo Simulação: 'pywin32' não instalado. Os cupons serão exibidos no console.")

print("=" * 60)
print("Vigia de pedidos iniciado. Pressione Ctrl+C para encerrar.\n")


def imprimir_cupom_texto(texto_cupom, pedido_id):
    """Envia o texto formatado para a impressora do Windows"""
    if not WIN32_DISPONIVEL:
        print(f"\n--- [SIMULAÇÃO DE IMPRESSÃO - PEDIDO #{pedido_id}] ---")
        print(texto_cupom)
        print("--- [FIM DA IMPRESSÃO] ---\n")
        return True

    try:
        impressora = win32print.GetDefaultPrinter()
        
        # Cria um arquivo temporário para enviar ao spooler do Windows
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(texto_cupom)
            temp_path = f.name

        print(f"🖨️ Enviando comanda #{pedido_id} para '{impressora}'...")
        win32api.ShellExecute(0, "print", temp_path, f'/d:"{impressora}"', ".", 0)
        
        # Aguarda brevemente para o spooler ler o arquivo antes de apagar
        time.sleep(2)
        try:
            os.remove(temp_path)
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"❌ Erro ao imprimir pedido #{pedido_id}: {e}")
        return False


def buscar_pedidos_pendentes():
    url = f"{SERVER_URL}/api/agente/pedidos/pendentes"
    req = urllib.request.Request(url, headers={
        'X-Printer-Token': PRINTER_TOKEN,
        'User-Agent': 'DogaoPrinterAgent/1.0'
    })

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                dados = json.loads(response.read().decode('utf-8'))
                if dados.get('success'):
                    return dados.get('pedidos', [])
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("❌ Erro 401: Token de impressão não autorizado. Verifique o PRINTER_TOKEN.")
        else:
            print(f"⚠️ Erro HTTP do servidor ({e.code}): {e.reason}")
    except urllib.error.URLError as e:
        # Falha de conexão normal se a internet cair temporariamente
        pass
    except Exception as e:
        print(f"⚠️ Erro inesperado ao consultar servidor: {e}")

    return []


def confirmar_impressao(pedido_id):
    url = f"{SERVER_URL}/api/agente/pedidos/{pedido_id}/confirmar-impressao"
    req = urllib.request.Request(url, data=b"{}", headers={
        'X-Printer-Token': PRINTER_TOKEN,
        'Content-Type': 'application/json',
        'User-Agent': 'DogaoPrinterAgent/1.0'
    }, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return True
    except Exception as e:
        print(f"⚠️ Erro ao confirmar impressão do pedido #{pedido_id}: {e}")

    return False


def main():
    while True:
        try:
            pedidos = buscar_pedidos_pendentes()
            if pedidos:
                print(f"\n🔔 {len(pedidos)} novo(s) pedido(s) aguardando impressão!")
                for p in pedidos:
                    pedido_id = p['id']
                    cliente = p.get('cliente', '')
                    cupom_texto = p.get('cupom_texto', '')

                    print(f"-> Processando Pedido #{pedido_id} ({cliente})...")
                    sucesso = imprimir_cupom_texto(cupom_texto, pedido_id)
                    
                    if sucesso:
                        if confirmar_impressao(pedido_id):
                            print(f"✅ Pedido #{pedido_id} impresso e confirmado com sucesso no servidor!")
                        else:
                            print(f"⚠️ Pedido #{pedido_id} foi impresso, mas não foi possível confirmar com o servidor.")
                    else:
                        print(f"❌ Falha ao imprimir Pedido #{pedido_id}. Ele continuará na fila.")

            time.sleep(INTERVALO_POLLING)

        except KeyboardInterrupt:
            print("\nAgente de impressão finalizado pelo operador.")
            sys.exit(0)
        except Exception as e:
            print(f"Erro no loop do agente: {e}")
            time.sleep(5)


if __name__ == '__main__':
    main()
