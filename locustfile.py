from locust import HttpUser, task, between
import random

class PlayerUser(HttpUser):
    """Симуляция игрока"""
    wait_time = between(1, 3)  # Ждём 1-3 секунды между действиями
    
    @task(3)
    def get_player(self):
        """Получить данные игрока"""
        chat_id = f"test_user_{random.randint(1, 100)}"
        self.client.get(f"/api/player/{chat_id}")
    
    @task(5)
    def click(self):
        """Сделать клик"""
        chat_id = f"test_user_{random.randint(1, 100)}"
        self.client.post(f"/api/click/{chat_id}")
    
    @task(2)
    def get_shop(self):
        """Посмотреть магазин"""
        self.client.get("/api/shop")
    
    @task(1)
    def get_boss(self):
        """Посмотреть босса"""
        self.client.get("/api/boss_status")
    
    @task(1)
    def get_achievements(self):
        """Посмотреть достижения"""
        self.client.get("/api/achievements")

class HeavyUser(HttpUser):
    """Активный пользователь (нагружает систему)"""
    wait_time = between(0.5, 1)
    
    @task(10)
    def rapid_click(self):
        """Быстрые клики"""
        chat_id = f"heavy_user_{random.randint(1, 50)}"
        self.client.post(f"/api/click/{chat_id}")
    
    @task(2)
    def check_stats(self):
        """Проверить статистику"""
        self.client.get("/api/stats")
cat << 'EOF' > locustfile.py
from locust import HttpUser, task, between
import random

class PlayerUser(HttpUser):
    """Симуляция игрока"""
    wait_time = between(1, 3)  # Ждём 1-3 секунды между действиями
    
    @task(3)
    def get_player(self):
        """Получить данные игрока"""
        chat_id = f"test_user_{random.randint(1, 100)}"
        self.client.get(f"/api/player/{chat_id}")
    
    @task(5)
    def click(self):
        """Сделать клик"""
        chat_id = f"test_user_{random.randint(1, 100)}"
        self.client.post(f"/api/click/{chat_id}")
    
    @task(2)
    def get_shop(self):
        """Посмотреть магазин"""
        self.client.get("/api/shop")
    
    @task(1)
    def get_boss(self):
        """Посмотреть босса"""
        self.client.get("/api/boss_status")
    
    @task(1)
    def get_achievements(self):
        """Посмотреть достижения"""
        self.client.get("/api/achievements")

class HeavyUser(HttpUser):
    """Активный пользователь (нагружает систему)"""
    wait_time = between(0.5, 1)
    
    @task(10)
    def rapid_click(self):
        """Быстрые клики"""
        chat_id = f"heavy_user_{random.randint(1, 50)}"
        self.client.post(f"/api/click/{chat_id}")
    
    @task(2)
    def check_stats(self):
        """Проверить статистику"""
        self.client.get("/api/stats")
cd ~/corp-bot-webapp

cat << 'EOF' > locustfile.py
from locust import HttpUser, task, between
import random

class PlayerUser(HttpUser):
    """Симуляция обычного игрока"""
    wait_time = between(1, 3)
    
    @task(3)
    def get_player(self):
        """Получить данные игрока"""
        chat_id = f"test_user_{random.randint(1, 100)}"
        self.client.get(f"/api/player/{chat_id}")
    
    @task(5)
    def click(self):
        """Сделать клик"""
        chat_id = f"test_user_{random.randint(1, 100)}"
        self.client.post(f"/api/click/{chat_id}")
    
    @task(2)
    def get_shop(self):
        """Посмотреть магазин"""
        self.client.get("/api/shop")
    
    @task(1)
    def get_boss(self):
        """Посмотреть босса"""
        self.client.get("/api/boss_status")
    
    @task(1)
    def get_achievements(self):
        """Посмотреть достижения"""
        self.client.get("/api/achievements")

class HeavyUser(HttpUser):
    """Активный пользователь (нагружает систему)"""
    wait_time = between(0.5, 1)
    
    @task(10)
    def rapid_click(self):
        """Быстрые клики"""
        chat_id = f"heavy_user_{random.randint(1, 50)}"
        self.client.post(f"/api/click/{chat_id}")
    
    @task(2)
    def check_stats(self):
        """Проверить статистику"""
        self.client.get("/api/stats")

class APIUser(HttpUser):
    """Пользователь который тестирует все endpoints"""
    wait_time = between(2, 5)
    
    @task(1)
    def health_check(self):
        """Проверка здоровья API"""
        self.client.get("/health")
    
    @task(1)
    def get_stats(self):
        """Получить статистику"""
        self.client.get("/api/stats")
    
    @task(1)
    def get_leaderboard(self):
        """Получить таблицу лидеров"""
        self.client.get("/api/leaderboard")
