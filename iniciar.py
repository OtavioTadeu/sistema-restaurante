import os
import sys
import subprocess
import time

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DOMAIN_FILE = os.path.join(BASE_DIR, 'ngrok_domain.txt')
NGROK_EXE = os.path.join(BASE_DIR, 'ngrok.exe')
CLOUDFLARED_EXE = os.path.join(BASE_DIR, 'cloudflared.exe')

def get_python_cmd():
    venv_py = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
    if os.path.exists(venv_py):
        return f'"{venv_py}"'
    return sys.executable

def start_window(title, command, color="0A"):
    # Abre uma janela CMD independente no Windows
    full_cmd = f'start "{title}" cmd /k "chcp 65001 > nul && title {title} && color {color} && {command}"'
    subprocess.Popen(full_cmd, shell=True, cwd=BASE_DIR)

def get_ngrok_domain():
    if os.path.exists(DOMAIN_FILE):
        with open(DOMAIN_FILE, 'r', encoding='utf-8') as f:
            dom = f.read().strip()
            if dom:
                return dom
    return None

def set_ngrok_domain(dom):
    with open(DOMAIN_FILE, 'w', encoding='utf-8') as f:
        f.write(dom.strip())

def menu_config_ngrok():
    print("\n" + "=" * 64)
    print("      CONFIGURAÇÃO DO NGROK (DOMÍNIO FIXO GRATUITO)")
    print("=" * 64)
    print("\n1. Authtoken:")
    print("   Obtenha gratuitamente em: https://dashboard.ngrok.com/get-started/your-authtoken")
    token = input("   Cole seu authtoken (ou Enter para pular): ").strip()
    if token:
        try:
            res = subprocess.run([NGROK_EXE, 'config', 'add-authtoken', token], capture_output=True, text=True)
            if res.returncode == 0:
                print("   [OK] Token configurado com sucesso!")
            else:
                print(f"   [AVISO] Erro ao salvar token: {res.stderr}")
        except Exception as e:
            print(f"   [ERRO] Falha ao executar ngrok: {e}")

    print("\n2. Domínio Estático Gratuito:")
    print("   Resgate em: https://dashboard.ngrok.com/cloud-edge/domains")
    print("   Exemplo: dogaocastelo.ngrok-free.app")
    atual = get_ngrok_domain()
    if atual:
        print(f"   (Domínio atual: {atual})")
    novo_dom = input("   Digite o domínio desejado (ou Enter para manter): ").strip()
    if novo_dom:
        # Remover eventual https:// ou http://
        novo_dom = novo_dom.replace('https://', '').replace('http://', '').strip('/')
        set_ngrok_domain(novo_dom)
        print(f"   [OK] Domínio salvo com sucesso: {novo_dom}")

    input("\nPressione Enter para voltar ao menu principal...")

def iniciar_com_ngrok():
    py = get_python_cmd()
    dom = get_ngrok_domain()
    if not dom:
        print("\n[!] Domínio estático do Ngrok ainda não foi informado.")
        print("    Resgate seu domínio em: https://dashboard.ngrok.com/cloud-edge/domains")
        dom = input("    Digite seu domínio (ex: seunome.ngrok-free.app): ").strip()
        if not dom:
            print("Operação cancelada.")
            time.sleep(2)
            return
        dom = dom.replace('https://', '').replace('http://', '').strip('/')
        set_ngrok_domain(dom)

    print("\nIniciando serviços...")
    print("  1/3 -> Servidor Flask (app.py)")
    start_window("Dogão - Servidor Flask", f"{py} app.py", color="0A")

    print("  2/3 -> Vigia de Impressão (impressor.py)")
    start_window("Dogão - Impressor de Comandas", f"{py} impressor.py", color="0B")

    print(f"  3/3 -> Túnel Ngrok ({dom})")
    start_window("Dogão - Túnel Ngrok", f'"{NGROK_EXE}" http --url={dom} 5000', color="0E")

    print("\n" + "=" * 64)
    print("  🚀 SISTEMA INICIADO COM SUCESSO!")
    print("=" * 64)
    print(f"  👉 Link do Cardápio para Clientes: https://{dom}")
    print(f"  👉 Painel Administrativo:          https://{dom}/admin")
    print("=" * 64)
    print("  Mantenha as 3 janelas abertas durante todo o expediente.")
    input("\nPressione Enter para voltar ao menu...")

def iniciar_com_cloudflare():
    py = get_python_cmd()
    print("\nIniciando serviços...")
    print("  1/3 -> Servidor Flask (app.py)")
    start_window("Dogão - Servidor Flask", f"{py} app.py", color="0A")

    print("  2/3 -> Vigia de Impressão (impressor.py)")
    start_window("Dogão - Impressor de Comandas", f"{py} impressor.py", color="0B")

    print("  3/3 -> Túnel Cloudflare (Quick Tunnel)")
    start_window("Dogão - Túnel Cloudflare", f'"{CLOUDFLARED_EXE}" tunnel --url http://localhost:5000', color="0E")

    print("\n" + "=" * 64)
    print("  🚀 SISTEMA INICIADO COM CLOUDFLARE!")
    print("=" * 64)
    print("  Copie o link temporário que foi gerado na janela amarela do Cloudflare.")
    print("=" * 64)
    input("\nPressione Enter para voltar ao menu...")

def iniciar_local():
    py = get_python_cmd()
    print("\nIniciando serviços locais...")
    print("  1/2 -> Servidor Flask (app.py)")
    start_window("Dogão - Servidor Flask", f"{py} app.py", color="0A")

    print("  2/2 -> Vigia de Impressão (impressor.py)")
    start_window("Dogão - Impressor de Comandas", f"{py} impressor.py", color="0B")

    print("\n" + "=" * 64)
    print("  🚀 SISTEMA LOCAL INICIADO!")
    print("=" * 64)
    print("  Acesse no computador da loja: http://localhost:5000")
    print("=" * 64)
    input("\nPressione Enter para voltar ao menu...")

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        dom = get_ngrok_domain()
        dom_info = f" ({dom})" if dom else " (Não configurado)"
        print("=" * 64)
        print("          🌭 DOGÃO DO CASTELO - CENTRAL DO SISTEMA 🌭")
        print("=" * 64)
        print(f"\n [1] Iniciar com NGROK (Domínio Fixo){dom_info}")
        print(" [2] Iniciar com CLOUDFLARE (Link temporário direto)")
        print(" [3] Iniciar Apenas Localmente (Sem internet)")
        print(" [4] Configurar Token ou Domínio do Ngrok")
        print(" [5] Sair")
        print("\n" + "=" * 64)

        opcao = input(" Digite a opção desejada [1-5] (Padrão: 1): ").strip()
        if not opcao:
            opcao = "1"

        if opcao == "1":
            iniciar_com_ngrok()
        elif opcao == "2":
            iniciar_com_cloudflare()
        elif opcao == "3":
            iniciar_local()
        elif opcao == "4":
            menu_config_ngrok()
        elif opcao == "5":
            print("\nAté logo!")
            break

if __name__ == '__main__':
    main()
