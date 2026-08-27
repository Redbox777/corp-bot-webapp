import json
from config import config
from database import update_player

def get_upgrade_price(upgrade_id, count):
    """Рассчитать цену улучшения"""
    upgrade = config.UPGRADES.get(upgrade_id)
    if not upgrade:
        return 0
    return int(upgrade["cost"] * (1.15 ** count))

def buy_upgrade(player, upgrade_id):
    """Купить улучшение"""
    if upgrade_id not in config.UPGRADES:
        return None, "Invalid upgrade"
    
    upgrades = player.get("upgrades") or {}
    count = upgrades.get(upgrade_id, 0)
    price = get_upgrade_price(upgrade_id, count)
    
    if player.get("balance", 0) < price:
        return None, "Недостаточно денег"
    
    # Применяем улучшение
    upgrade = config.UPGRADES[upgrade_id]
    new_upgrades = {**upgrades, upgrade_id: count + 1}
    
    new_click_power = (player.get("click_power") or 10)
    new_passive_income = (player.get("passive_income") or 0)
    
    if upgrade["type"] == "click":
        new_click_power += upgrade.get("power", 0)
    else:
        new_passive_income += upgrade.get("income", 0)
    
    # Обновляем игрока
    update_player(
        player["chat_id"],
        balance=player["balance"] - price,
        upgrades=json.dumps(new_upgrades),
        click_power=new_click_power,
        passive_income=new_passive_income,
        last_update=__import__('time').time()
    )
    
    return {
        "balance": player["balance"] - price,
        "click_power": new_click_power,
        "passive_income": new_passive_income,
        "upgrades": new_upgrades,
        "success": True
    }, None
