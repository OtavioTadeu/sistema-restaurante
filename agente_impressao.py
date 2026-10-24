"""
Agente de Impressão Local — Dogão do Castelo
Este executável roda no computador do caixa/balcão do restaurante onde a impressora está conectada.
Ele consulta os novos pedidos na Nuvem e imprime diretamente na impressora térmica do Windows.
Não requer instalação do Python na máquina de destino.
"""

import os
import sys
import time
import tempfile
import urllib.request
import urllib.error
import json
import configparser

# Suporte nativo a impressão no Windows
try:
    import win32api
    import win32print
    WIN32_DISPONIVEL = True
except ImportError:
    WIN32_DISPONIVEL = False

# Determina o diretório base (mesmo quando empacotado como .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, 'config.ini')

# Cria o arquivo config.ini com valores padrão se não existir
if not os.path.exists(CONFIG_PATH):
    novo_config = configparser.ConfigParser()
    novo_config['DOGAO'] = {
        'SERVER_URL': 'https://dogao-do-castelo.onrender.com',
        'PRINTER_TOKEN': 'dogao_printer_sec_9a8b7c6d5e4f3a2b1c0d',
        'INTERVALO_POLLING': '4',
        'NOME_IMPRESSORA': ''
    }
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write("# ============================================================\n")
            f.write("# CONFIGURAÇÃO DO AGENTE DE IMPRESSÃO - DOGÃO DO CASTELO\n")
            f.write("# ============================================================\n")
            f.write("# Altere este arquivo caso mude a URL do servidor ou o token.\n\n")
            novo_config.write(f)
    except Exception as e:
        print(f"Aviso: Não foi possível criar config.ini inicial: {e}")

# Valores padrão de fábrica
SERVER_URL = 'https://dogao-do-castelo.onrender.com'
PRINTER_TOKEN = 'dogao_printer_sec_9a8b7c6d5e4f3a2b1c0d'
INTERVALO_POLLING = 4
NOME_IMPRESSORA = ''

# Lê config.ini se existir
if os.path.exists(CONFIG_PATH):
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH, encoding='utf-8')
        if 'DOGAO' in config:
            SERVER_URL = config['DOGAO'].get('SERVER_URL', SERVER_URL).strip().rstrip('/')
            PRINTER_TOKEN = config['DOGAO'].get('PRINTER_TOKEN', PRINTER_TOKEN).strip()
            INTERVALO_POLLING = int(config['DOGAO'].get('INTERVALO_POLLING', str(INTERVALO_POLLING)))
            NOME_IMPRESSORA = config['DOGAO'].get('NOME_IMPRESSORA', '').strip()
    except Exception as e:
        print(f"Aviso ao ler config.ini: {e}")

# Tenta carregar .env local como alternativa se existir
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH)
        SERVER_URL = os.getenv('SERVER_URL', SERVER_URL).rstrip('/')
        PRINTER_TOKEN = os.getenv('PRINTER_TOKEN', PRINTER_TOKEN)
    except Exception:
        pass


def obter_impressora_alvo():
    """Retorna o nome da impressora a ser utilizada"""
    if NOME_IMPRESSORA:
        return NOME_IMPRESSORA
    if WIN32_DISPONIVEL:
        try:
            return win32print.GetDefaultPrinter()
        except Exception:
            return None
    return None


def imprimir_cupom_texto(texto_cupom, pedido_id):
    """
    Imprime o texto da comanda.
    Tenta primeiro envio direto ao Spooler RAW (sem popup).
    Caso falhe, utiliza ShellExecute como fallback.
    """
    if not WIN32_DISPONIVEL:
        print(f"\n--- [SIMULAÇÃO DE IMPRESSÃO - PEDIDO #{pedido_id}] ---")
        print(texto_cupom)
        print("--- [FIM DA IMPRESSÃO] ---\n")
        return True

    impressora = obter_impressora_alvo()
    if not impressora:
        print(f"❌ Nenhuma impressora encontrada no Windows para o Pedido #{pedido_id}.")
        return False

    # Método 1: Envio direto RAW para a impressora (mais rápido e sem janelas do Notepad)
    try:
        hPrinter = win32print.OpenPrinter(impressora)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, (f"Comanda Dogao #{pedido_id}", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                # Tenta codificação cp850 / latin1 comum em impressoras térmicas brasileiras
                dados_bytes = texto_cupom.encode('cp850', errors='replace')
                # Adiciona corte de papel / alimentação final (LF extra)
                dados_bytes += b"\n\n\n\n\x1b\x69"  # ESC i (corte de papel comum) ou quebras
                win32print.WritePrinter(hPrinter, dados_bytes)
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)

        print(f"🖨️  Comanda #{pedido_id} enviada via spooler direto para '{impressora}'.")
        return True

    except Exception as erro_raw:
        print(f"⚠️ Spooler direto falhou ({erro_raw}). Tentando método alternativo via Shell...")

    # Método 2: Fallback via ShellExecute
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(texto_cupom)
            temp_path = f.name

        win32api.ShellExecute(0, "print", temp_path, f'/d:"{impressora}"', ".", 0)
        time.sleep(2)
        try:
            os.remove(temp_path)
        except Exception:
            pass
        print(f"🖨️  Comanda #{pedido_id} enviada via Shell para '{impressora}'.")
        return True
    except Exception as erro_shell:
        print(f"❌ Falha ao imprimir Pedido #{pedido_id}: {erro_shell}")
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
            print("\n❌ ERRO 401 - NÃO AUTORIZADO:")
            print("   O token de impressão configurado no 'config.ini' não coincide")
            print("   com a variável PRINTER_TOKEN no servidor da nuvem (Render).")
            print("   Verifique o painel do Render > Environment > PRINTER_TOKEN.")
            time.sleep(6)
        else:
            print(f"⚠️ Erro HTTP do servidor ({e.code}): {e.reason}")
    except urllib.error.URLError as e:
        # Perda temporária de conexão
        pass
    except Exception as e:
        print(f"⚠️ Erro na consulta ao servidor: {e}")

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
        print(f"⚠️ Erro ao confirmar impressão no servidor para o pedido #{pedido_id}: {e}")

    return False


def main():
    print("=" * 64)
    print("         DOGÃO DO CASTELO — AGENTE DE IMPRESSÃO LOCAL")
    print("=" * 64)
    print(f"📡 Conectando ao Servidor : {SERVER_URL}")
    print(f"⏱️  Intervalo de Checagem  : {INTERVALO_POLLING}s")

    impressora_atual = obter_impressora_alvo()
    if WIN32_DISPONIVEL and impressora_atual:
        print(f"🖨️  Impressora do Windows : {impressora_atual}")
    elif WIN32_DISPONIVEL:
        print("⚠️  Nenhuma impressora padrão configurada no Windows.")
    else:
        print("⚠️  Modo Simulação (Cupons serão exibidos na tela).")

    print(f"📁 Pasta de Configuração  : {BASE_DIR}")
    print("=" * 64)
    print("Vigia de pedidos iniciado. Mantenha esta janela aberta no balcão.\n")

    while True:
        try:
            pedidos = buscar_pedidos_pendentes()
            if pedidos:
                print(f"\n🔔 {len(pedidos)} novo(s) pedido(s) aguardando impressão!")
                for p in pedidos:
                    pedido_id = p.get('id')
                    cliente = p.get('cliente', '')
                    cupom_texto = p.get('cupom_texto', '')

                    print(f"-> Imprimindo Pedido #{pedido_id} ({cliente})...")
                    sucesso = imprimir_cupom_texto(cupom_texto, pedido_id)

                    if sucesso:
                        if confirmar_impressao(pedido_id):
                            print(f"✅ Pedido #{pedido_id} impresso e confirmado com sucesso no servidor!")
                        else:
                            print(f"⚠️ Pedido #{pedido_id} foi impresso, mas aguardando reconexão com servidor.")
                    else:
                        print(f"❌ Não foi possível imprimir o Pedido #{pedido_id}. Ele permanecerá na fila.")

            time.sleep(INTERVALO_POLLING)

        except KeyboardInterrupt:
            print("\nAgente finalizado pelo operador.")
            break
        except Exception as e:
            print(f"Erro no ciclo do agente: {e}")
            time.sleep(5)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nErro crítico: {e}")
        input("\nPressione Enter para fechar...")
