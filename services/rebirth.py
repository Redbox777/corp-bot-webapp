from config import config
from database import update_player

def can_rebirth(player):
    """Проверить возможность перерождения"""
    level = player.get("level") or 1
    total_earned = player.get("total_earned") or 0
    return level >= config.REBIRTH_THRESHOLD_LEVEL or total_earned >= config.REBIRTH_THRESHOLD_EARNED

def do_rebirth(player):
    """Выполнить перерождение"""
    if not can_rebirth(player):
        return None, f"Нужен {config.REBIRTH_THRESHOLD_LEVEL} уровень или {config.REBIRTH_THRESHOLD_EARNED}$ всего"
    
    # Расчет кристаллов
    current_gems = player.get("prestige_points") or 0
    total_earned = player.get("total_earned") or 0
    
    gems_to_add = max(1, (total_earned // 5000) - current_gems)
    new_total_gems = current_gems + gems_to_add
    new_mult = 1.0 + (new_total_gems * config.PRESTIGE_MULTIPLIER)
    new_prestiges = (player.get("total_prestiges") or 0) + 1
    
    # Сброс прогресса
    update_player(
        player["chat_id"],
        balance=0,
        clicks=0,
        level=1,
        passive_income=0,
        click_power=10,
        upgrades='{}',
        total_earned=0,
        prestige_points=new_total_gems,
        prestige_mult=new_mult,
        total_prestiges=new_prestiges,
        last_update=__import__('time').time()
    )
    
    return {
        "success": True,
        "gems_added": gems_to_add,
        "total_gems": new_total_gems,
        "multiplier": new_mult,
        "message": f"Перерождение успешно! +{gems_to_add} 💎"
    }, None
