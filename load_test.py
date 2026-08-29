#!/usr/bin/env python3
"""
Простой нагрузочный тест (без Locust)
"""
import requests
import time
import threading
from datetime import datetime
import random

class LoadTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0,
            "errors": []
        }
        self.lock = threading.Lock()
    
    def make_request(self, endpoint, method="GET"):
        """Сделать запрос"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            elapsed = time.time() - start_time
            
            with self.lock:
                self.stats["total_requests"] += 1
                self.stats["total_time"] += elapsed
                
                if response.status_code == 200:
                    self.stats["successful"] += 1
                else:
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"{endpoint}: {response.status_code}")
        
        except Exception as e:
            with self.lock:
                self.stats["total_requests"] += 1
                self.stats["failed"] += 1
                self.stats["errors"].append(f"{endpoint}: {str(e)}")
    
    def simulate_user(self, user_id, num_requests=10):
        """Симуляция пользователя"""
        endpoints = [
            ("/api/player/test_user_", "GET"),
            ("/api/click/test_user_", "POST"),
            ("/api/shop", "GET"),
            ("/api/boss_status", "GET"),
            ("/api/achievements", "GET"),
        ]
        
        for i in range(num_requests):
            endpoint, method = random.choice(endpoints)
            if "test_user" in endpoint:
                endpoint = f"{endpoint}{user_id}_{i}"
            
            self.make_request(endpoint, method)
            time.sleep(random.uniform(0.1, 0.5))
    
    def run_test(self, num_users=10, requests_per_user=20):
        """Запустить тест"""
        print(f" Starting load test...")
        print(f"   Users: {num_users}")
        print(f"   Requests per user: {requests_per_user}")
        print(f"   Total requests: ~{num_users * requests_per_user}")
        print()
        
        start_time = time.time()
        threads = []
        
        for i in range(num_users):
            t = threading.Thread(target=self.simulate_user, args=(i, requests_per_user))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        total_time = time.time() - start_time
        
        self.print_results(total_time)
    
    def print_results(self, total_time):
        """Вывести результаты"""
        print("\n" + "="*50)
        print("📊 LOAD TEST RESULTS")
        print("="*50)
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Total requests: {self.stats['total_requests']}")
        print(f"Successful: {self.stats['successful']} ({self.stats['successful']/self.stats['total_requests']*100:.1f}%)")
        print(f"Failed: {self.stats['failed']} ({self.stats['failed']/self.stats['total_requests']*100:.1f}%)")
        print(f"Requests/sec: {self.stats['total_requests']/total_time:.2f}")
        print(f"Average response time: {self.stats['total_time']/self.stats['total_requests']*1000:.2f} ms")
        
        if self.stats['errors']:
            print(f"\n⚠️  Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:5]:  # Показать первые 5 ошибок
                print(f"   - {error}")
        
        print("="*50)

if __name__ == "__main__":
    test = LoadTest("http://localhost:5000")
    test.run_test(num_users=10, requests_per_user=20)
