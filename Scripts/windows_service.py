#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
windows_service.py
------------------
Bu modül, Windows üzerinde çalışan ve sistem istatistiklerini (CPU, GPU, bellek) 
toplayarak bir socket üzerinden yayınlayan bir servis uygulaması örneğidir.
"""

import socket
import time
import psutil
import json

try:
    from py3nvml.py3nvml import nvmlInit, nvmlShutdown, nvmlDeviceGetHandleByIndex, nvmlDeviceGetUtilizationRates
    GPU_AVAILABLE = True
except ImportError:
    print("py3nvml bulunamadı veya yüklenemedi. GPU bilgisi alınamayacak.")
    GPU_AVAILABLE = False


class SystemStats:
    """
    Bilgisayarın CPU, GPU ve bellek kullanımını ölçen sınıf.
    """

    def __init__(self):
        # NVIDIA GPU erişimi için başlatma
        if GPU_AVAILABLE:
            nvmlInit()

    def get_cpu_usage(self):
        """
        CPU kullanım yüzdesini döndürür.
        """
        return psutil.cpu_percent(interval=None)

    def get_memory_usage(self):
        """
        Bellek kullanım yüzdesini döndürür.
        """
        mem_info = psutil.virtual_memory()
        return mem_info.percent

    def get_gpu_usage(self):
        """
        GPU kullanım yüzdesini döndürür (NVIDIA GPU'lar için).
        Eğer GPU_AVAILABLE False ise, -1 döndürüyoruz.
        """
        if not GPU_AVAILABLE:
            return -1

        handle = nvmlDeviceGetHandleByIndex(0)  # 0. GPU'yu hedefliyoruz
        utilization = nvmlDeviceGetUtilizationRates(handle)
        return utilization.gpu

    def collect_stats(self):
        """
        Tüm verileri toplayıp sözlük olarak döndürür.
        """
        return {
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "gpu_usage": self.get_gpu_usage()
        }

    def __del__(self):
        """
        Nesne yok edilirken GPU kullanımını sonlandır.
        """
        if GPU_AVAILABLE:
            nvmlShutdown()


class StatsServer:
    """
    Windows üzerinde çalışan bir TCP sunucusu olup, istemciye belirli aralıklarla
    sistem istatistiklerini gönderir.
    """

    def __init__(self, host="0.0.0.0", port=5000, interval=2):
        """
        Sunucu nesnesini başlatır.
        :param host: Sunucu IP adresi, varsayılan 0.0.0.0 (tüm arayüzler).
        :param port: Sunucu portu, varsayılan 5000.
        :param interval: Kaç saniyede bir veri gönderileceği, varsayılan 2 saniye.
        """
        self.host = host
        self.port = port
        self.interval = interval
        self.stats = SystemStats()

    def start_server(self):
        """
        Soket oluşturur ve gelen bağlantıları dinlemeye başlar.
        Bağlanan ilk istemciye periyodik olarak sistem istatistiklerini gönderir.
        """
        # TCP/IPv4 soketi oluşturma
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print(f"Sunucu başlatıldı: {self.host}:{self.port}")
            print("İstemci bağlantısı bekleniyor...")

            # Bir istemci bağlandığında accept edeceğiz:
            client_socket, client_address = server_socket.accept()
            with client_socket:
                print(f"Bağlanan istemci: {client_address}")

                # Sürekli olarak verileri istemciye gönder
                while True:
                    stats_data = self.stats.collect_stats()
                    # JSON formatına çevirip gönderiyoruz
                    json_data = json.dumps(stats_data)
                    client_socket.sendall((json_data + "\n").encode('utf-8'))

                    # 2 saniye bekleme
                    time.sleep(self.interval)


if __name__ == "__main__":
    # Sunucuyu başlatalım
    server = StatsServer(host="0.0.0.0", port=5000, interval=2)
    server.start_server()
