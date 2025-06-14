import requests
import psutil
import platform
import socket
import subprocess
import time
import threading
from datetime import datetime
import json

# Configuração do webhook
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1383322708011388988/UDgAynqBeWvdWdOn2olV5zmeKUlpdOxH8tQCdWPsE8TvS58YsjTO4H2mndERe3kSlQFP"  # Substitua pela sua URL do webhook

def get_internet_speed():
    """Testa a velocidade da internet usando speedtest-cli"""
    try:
        result = subprocess.run(['speedtest-cli', '--simple'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            ping = lines[0].split(': ')[1] if 'Ping:' in lines[0] else 'N/A'
            download = lines[1].split(': ')[1] if 'Download:' in lines[1] else 'N/A'
            upload = lines[2].split(': ')[1] if 'Upload:' in lines[2] else 'N/A'
            return ping, download, upload
    except:
        pass
    return 'N/A', 'N/A', 'N/A'

def get_ping_to_google():
    """Testa ping para o Google"""
    try:
        result = subprocess.run(['ping', '-c', '4', '8.8.8.8'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'avg' in line or 'min/avg/max' in line:
                    return line.split('/')[-3] + ' ms'
    except:
        pass
    return 'N/A'

def get_system_info():
    """Coleta informações detalhadas do sistema"""
    # Informações básicas
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Sistema operacional
    distro = f"{platform.system()} {platform.release()}"
    if platform.system() == "Linux":
        try:
            with open('/etc/os-release', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('PRETTY_NAME='):
                        distro = line.split('=')[1].strip().strip('"')
                        break
        except:
            pass
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    cpu_freq_current = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
    
    # Memória
    memory = psutil.virtual_memory()
    memory_total = f"{memory.total / (1024**3):.1f} GB"
    memory_used = f"{memory.used / (1024**3):.1f} GB"
    memory_percent = memory.percent
    
    # Disco
    disk = psutil.disk_usage('/')
    disk_total = f"{disk.total / (1024**3):.1f} GB"
    disk_used = f"{disk.used / (1024**3):.1f} GB"
    disk_percent = (disk.used / disk.total) * 100
    
    # Uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
    
    # Rede
    network = psutil.net_io_counters()
    bytes_sent = f"{network.bytes_sent / (1024**2):.1f} MB"
    bytes_recv = f"{network.bytes_recv / (1024**2):.1f} MB"
    
    # Temperatura (se disponível)
    temp = "N/A"
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    temp = f"{entries[0].current:.1f}°C"
                    break
    except:
        pass
    
    # Teste de velocidade da internet
    ping_speed, download_speed, upload_speed = get_internet_speed()
    
    # Ping para Google
    google_ping = get_ping_to_google()
    
    return {
        'hostname': hostname,
        'local_ip': local_ip,
        'distro': distro,
        'cpu_percent': cpu_percent,
        'cpu_count': cpu_count,
        'cpu_freq': cpu_freq_current,
        'memory_total': memory_total,
        'memory_used': memory_used,
        'memory_percent': memory_percent,
        'disk_total': disk_total,
        'disk_used': disk_used,
        'disk_percent': disk_percent,
        'uptime': uptime_str,
        'bytes_sent': bytes_sent,
        'bytes_recv': bytes_recv,
        'temperature': temp,
        'ping_speed': ping_speed,
        'download_speed': download_speed,
        'upload_speed': upload_speed,
        'google_ping': google_ping
    }

def create_discord_embed(system_info):
    """Cria o embed do Discord com as informações do sistema"""
    timestamp = datetime.now().isoformat()
    
    # Determina a cor baseada no status (verde = bom, amarelo = atenção, vermelho = crítico)
    color = 0x00FF00  # Verde padrão
    if system_info['cpu_percent'] > 80 or system_info['memory_percent'] > 80:
        color = 0xFFFF00  # Amarelo
    if system_info['cpu_percent'] > 95 or system_info['memory_percent'] > 95:
        color = 0xFF0000  # Vermelho
    
    embed = {
        "title": f"🖥️ Status da VPS - {system_info['hostname']}",
        "description": "Monitoramento automático do servidor",
        "color": color,
        "timestamp": timestamp,
        "thumbnail": {
            "url": "https://mdzero.com/wp-content/uploads/2025/03/vps.jpg"
        },
        "fields": [
            {
                "name": "🔧 Sistema",
                "value": f"**OS:** {system_info['distro']}\n**IP Local:** {system_info['local_ip']}\n**Uptime:** {system_info['uptime']}",
                "inline": True
            },
            {
                "name": "💻 CPU",
                "value": f"**Uso:** {system_info['cpu_percent']}%\n**Cores:** {system_info['cpu_count']}\n**Frequência:** {system_info['cpu_freq']}",
                "inline": True
            },
            {
                "name": "🧠 Memória",
                "value": f"**Uso:** {system_info['memory_percent']}%\n**Usada:** {system_info['memory_used']}\n**Total:** {system_info['memory_total']}",
                "inline": True
            },
            {
                "name": "💾 Disco",
                "value": f"**Uso:** {system_info['disk_percent']:.1f}%\n**Usado:** {system_info['disk_used']}\n**Total:** {system_info['disk_total']}",
                "inline": True
            },
            {
                "name": "🌐 Rede",
                "value": f"**Enviado:** {system_info['bytes_sent']}\n**Recebido:** {system_info['bytes_recv']}\n**Temp:** {system_info['temperature']}",
                "inline": True
            },
            {
                "name": "⚡ Internet",
                "value": f"**Download:** {system_info['download_speed']}\n**Upload:** {system_info['upload_speed']}\n**Ping (Speedtest):** {system_info['ping_speed']}",
                "inline": True
            },
            {
                "name": "🏓 Conectividade",
                "value": f"**Ping Google:** {system_info['google_ping']}\n**Status:** ✅ Online",
                "inline": False
            }
        ],
        "footer": {
            "text": f"Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}"
        }
    }
    
    return embed

def send_discord_webhook(embed):
    """Envia o webhook para o Discord"""
    try:
        payload = {
            "embeds": [embed]
        }
        
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 204:
            print(f"✅ Webhook enviado com sucesso - {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"❌ Erro ao enviar webhook: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao enviar webhook: {str(e)}")

def monitor_vps():
    """Função principal de monitoramento"""
    print("🚀 Iniciando monitoramento da VPS...")
    print("📡 Enviando relatórios a cada 5 minutos...")
    
    while True:
        try:
            print(f"\n📊 Coletando informações do sistema - {datetime.now().strftime('%H:%M:%S')}")
            system_info = get_system_info()
            embed = create_discord_embed(system_info)
            send_discord_webhook(embed)
            
            print("⏰ Aguardando 5 minutos para próximo envio...")
            time.sleep(300)  # 5 minutos = 300 segundos
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoramento interrompido pelo usuário")
            break
        except Exception as e:
            print(f"❌ Erro no monitoramento: {str(e)}")
            print("🔄 Tentando novamente em 1 minuto...")
            time.sleep(60)

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL == "YOUR_WEBHOOK_URL_HERE":
        print("⚠️  ATENÇÃO: Configure sua URL do webhook Discord na variável DISCORD_WEBHOOK_URL")
        print("📝 Edite o arquivo e substitua 'YOUR_WEBHOOK_URL_HERE' pela sua URL do webhook")
    else:
        monitor_vps()
