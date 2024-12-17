from db.user_db import get_user_balance, update_user_gold, get_user_power, update_user_max_health
from db.client import supabase


async def buy_hourly_upgrade(user_id, amount):
    if amount <= 0:
        return "Invalid amount."
    cost_per = 500
    total_cost = cost_per * amount
    current_gold = await get_user_balance(user_id)
    if current_gold < total_cost:
        return "You don't have enough gold."
    resp = supabase.table("users").select("hourly_multiplier").eq("id", user_id).execute()
    current_multi = resp.data[0]["hourly_multiplier"]
    new_multi = current_multi + (0.1 * amount)
    await update_user_gold(user_id, current_gold - total_cost)
    supabase.table("users").update({"hourly_multiplier": new_multi}).eq("id", user_id).execute()
    return f"Your hourly gold claim multiplier is now {new_multi:.2f}!"
