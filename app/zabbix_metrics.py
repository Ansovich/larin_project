import psutil
import socket

def get_system_metrics():
    """Собирает системные метрики для Zabbix"""
    return {
        'cpu.usage': psutil.cpu_percent(interval=1),
        'memory.used': psutil.virtual_memory().used / (1024 * 1024),  # MB
        'memory.free': psutil.virtual_memory().available / (1024 * 1024),  # MB
    }

def send_to_zabbix(hostname, metrics):
    """Отправляет метрики в Zabbix (заглушка для демонстрации)"""
    # В реальном проекте здесь будет отправка через zabbix_sender
    # Пример: zabbix_sender.send(hostname, metrics)
    print(f"[Zabbix] Sending metrics for {hostname}: {metrics}")
    return True
