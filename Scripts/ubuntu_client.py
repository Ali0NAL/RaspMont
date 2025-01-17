#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ubuntu_client.py
----------------
Bu modül, Ubuntu/Raspberry Pi gibi bir ortamda çalışarak Windows tarafındaki 
sunucu servisinden sistem istatistiklerini alır ve her 2 saniyede bir ekrana basar.
"""

import socket
import json

class StatsClient:
    """
    Bir TCP soketi üzerinden sunucudan gelen sistem istatistiklerini dinleyen istemci sınıfı.
    """

    def __init__(self, server_ip="192.168.1.230", port=5000):
        """
        İstemci nesnesini başlatır.
        :param server_ip: Bağlanılacak sunucunun IP adresi.
        :param port: Sunucu portu, varsayılan 5000.
        """
        self.server_ip = server_ip
        self.port = port
        self.client_socket = None

    def connect(self):
        """
        Sunucuya bağlanır.
        """
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.port))
        print(f"Sunucuya bağlanıldı: {self.server_ip}:{self.port}")

    def listen_data(self):
        """
        Sunucudan gelen JSON formatlı veri satırlarını dinler ve okur.
        Gelen veriyi ekrana bastırır.
        """
        try:
            with self.client_socket:
                buffer = b""
                while True:
                    chunk = self.client_socket.recv(1024)
                    if not chunk:
                        # Sunucu bağlantısını kapattı
                        print("Sunucu bağlantıyı kesti.")
                        break

                    buffer += chunk

                    # Veriler '\n' ile ayrıldığından, her newline'ı ayrı bir JSON olarak çözümlüyoruz
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                self.process_data(data)
                            except json.JSONDecodeError:
                                print("Gelen veride JSON hatası oluştu.")
        except KeyboardInterrupt:
            print("İstemci sonlandırıldı.")
        except ConnectionRefusedError:
            print("Sunucu bağlantısı reddedildi. Sunucu açık mı?")
        finally:
            if self.client_socket:
                self.client_socket.close()

    def process_data(self, data):
        """
        Sunucudan alınan veriyi işlemek için kullanılır.
        Örnek olarak sadece ekrana basıyoruz.
        """
        cpu = data.get("cpu_usage", -1)
        mem = data.get("memory_usage", -1)
        gpu = data.get("gpu_usage", -1)

        print(f"CPU Kullanımı: {cpu}%, Bellek Kullanımı: {mem}%, GPU Kullanımı: {gpu}%")

if __name__ == "__main__":
    client = StatsClient(server_ip="192.168.1.100", port=5000)  # Sunucunun IP'sini girin
    client.connect()
    client.listen_data()
