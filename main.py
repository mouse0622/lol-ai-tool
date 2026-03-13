from dotenv import load_dotenv
from google import genai
from google.genai import types
import tkinter as tk
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()
client = genai.Client()
language = "zh_TW"
latest_version = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
testing = 0
print(f"目前版本:{latest_version}")

def get_lol_items_advanced():
    # 1. 取得版本與資料
    version = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/zh_TW/item.json"
    data = requests.get(url).json().get("data", {})

    # 2. 定義數值對照表 (Stats Translation)
    stats_map = {
        "FlatPhysicalDamageMod": "物理攻擊",
        "FlatMagicDamageMod": "魔法攻擊",
        "FlatHPPoolMod": "生命值",
        "FlatMPPoolMod": "魔力值",
        "FlatArmorMod": "物理防禦",
        "FlatSpellBlockMod": "魔法防禦",
        "PercentAttackSpeedMod": "攻擊速度",
        "PercentMovementSpeedMod": "移動速度",
        "FlatMovementSpeedMod": "移動速度",
        "PercentCritChanceMod": "暴擊機率",
        "FlatCritChanceMod": "暴擊機率",
        "PercentLifeStealMod": "生命偷取",
        "FlatHPRegenMod": "生命回復",
        "FlatMPRegenMod": "魔力回復"
    }

    # 3. 定義分類標籤對照表 (Tags Translation)
    tags_map = {
        "Damage": "物理傷害", "SpellDamage": "魔法傷害", "SpellBlock": "魔防",
        "Armor": "物防", "Health": "生命值", "CriticalStrike": "暴擊",
        "AttackSpeed": "攻速", "LifeSteal": "吸血", "Mana": "魔力",
        "ManaRegen": "魔力回復", "HealthRegen": "生命回復", "AbilityHaste": "技能急速",
        "OnHit": "擊中效果", "AttackSpeed": "攻速", "Active": "主動技能",
        "Boots": "鞋子", "Consumable": "消耗品", "Stealth": "穿透/隱身"
    }

    result_list = []

    for item_id, item in sorted(data.items(), key=lambda x: x[1].get('gold', {}).get('total', 0)):
        # 過濾：召喚峽谷 (11) 且可購買
        if item.get("maps", {}).get("11") and item.get("gold", {}).get("purchasable"):
            name = item.get("name")
            gold = item.get("gold", {}).get("total", 0)
            
            # --- 處理數值 (Stats) ---
            stats_info = []
            raw_stats = item.get("stats", {})
            for key, value in raw_stats.items():
                stat_name = stats_map.get(key, key) # 若沒對照到則顯示原名
                # 處理百分比顯示
                if "Percent" in key:
                    stats_info.append(f"+{int(value * 100)}% {stat_name}")
                else:
                    stats_info.append(f"+{value} {stat_name}")
            stats_str = " | ".join(stats_info) if stats_info else "無基礎加成"

            # --- 處理分類 (Tags) ---
            tags = item.get("tags", [])
            translated_tags = [tags_map.get(t, t) for t in tags if t in tags_map]
            category_str = "、".join(translated_tags) if translated_tags else "一般"

            # --- 組合最終字串 ---
            item_entry = (
                f"【{name}】 ID: {item_id}\n"
                f"-分類: {category_str}\n"
                f"-價格: {gold}\n"
                f"-數值: {stats_str}\n"
                f"-簡介: {item.get('plaintext', '無')}\n"
                f"{'-'*50}"
            )
            result_list.append(item_entry)

    final_string = f"🚀 英雄聯盟召喚峽谷裝備庫 (版本: {version})\n\n" + "\n".join(result_list)
    return final_string

def get_champion_id_map():
    # 1. 獲取中文英雄資料庫
    all_champs_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/zh_TW/champion.json"
    raw_data = requests.get(all_champs_url).json()['data']
    
    # 2. 建立對照表： { "中文名稱": "英文ID" }
    # 注意：'name' 是中文顯示名稱, 'id' 是 DDragon 用的英文名稱
    name_to_id = {info['name']: info['id'] for _, info in raw_data.items()}
    
    return name_to_id


def get_matchup_data():
    champion_mapping = get_champion_id_map()
    try:
        response = requests.get("https://127.0.0.1:2999/liveclientdata/allgamedata", verify=False, timeout=2)
        if response.status_code != 200:
            return None
        
        data = response.json()
        all_players = data.get('allPlayers', [])
        active_player_name = data.get('activePlayer', {}).get('summonerName')
        
        # 1. 先找到「使用者」的資料
        me = next((p for p in all_players if p['summonerName'] == active_player_name), None)
        
        if not me:
            print("尚未找到玩家資料")
            return
        
        my_team = me['team']
        my_position = me['position'] # 例如: TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY

        # 2. 尋找敵方對位
        enemy_matchup = None
        for player in all_players:
            # 條件：陣營不同 且 位置相同
            if player['team'] != my_team and player['position'] == my_position:
                enemy_matchup = player
                break
        
        if enemy_matchup:
            print(f"你的對手是: {enemy_matchup['championName']}")
            print(f"對手裝備數: {len(enemy_matchup['items'])}")
            print(f"對手 KDA: {enemy_matchup['scores']['kills']}/{enemy_matchup['scores']['deaths']}/{enemy_matchup['scores']['assists']}")
        else:
            print("尚未偵測到敵方對位（可能在練習模式或特殊地圖）")
    except Exception as e:
        print("沒有正在進行的對局\n")
        return champion_mapping["Aatrox"],champion_mapping["Aatrox"]
    return [champion_mapping[me['championName']],champion_mapping[enemy_matchup['championName']]]

def check_current_state():
    if testing:
        return True
    try:
        response = requests.get("https://127.0.0.1:2999/liveclientdata/allgamedata", verify=False, timeout=2)
        return True
    except Exception:
        return False
    

def get_champion_data(target_champion = "Aatrox"):
    champion_data = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/{language}/champion/{target_champion}.json",timeout=2).json()
    tips = f"當你遊玩此角色:\n{"\n".join(champion_data["data"][target_champion]["allytips"])}\n當此角色在對面:\n{"\n".join(champion_data["data"][target_champion]["enemytips"])}\n"
    champion_role = "定位:" + ",".join(champion_data["data"][target_champion]["tags"]) + '\n'
    skill_description = ""
    spell = champion_data["data"][target_champion]["spells"]
    for cur in spell:
        skill_description += f"{cur["name"]}({cur["id"]}):{cur["description"]}\n"
    return f"{champion_data["data"][target_champion]["name"]}({champion_data["data"][target_champion]["title"]})" + champion_role + skill_description + tips

def gen_prompt():
    my_champion = "Akali"
    opponent_champion = "Ahri"
    if not testing:
        my_champion,opponent_champion = get_matchup_data()
    my_data = get_champion_data(my_champion)
    opponent_data = get_champion_data(opponent_champion)
    item_description = get_lol_items_advanced()
    ret = f"""我正在玩英雄聯盟，我的英雄是:\n\n{my_data}\n\n，而我對手則使用:\n\n{opponent_data}\n\n，請幫我生成一個簡單的純文字攻略(不要涉及表格等呈現方式，可以使用列點之類的)，講解一下如何面對比較好\n
    請使用以下格式生成回覆:\n
    -核心策略(可分為:開局、對線期、團戰，分別給出三句建議)\n
    -對手技能(分別約30字，簡要提到其重要效果)
    -推薦出裝策略(僅列出開局出裝、建議鞋子及前三件大裝(非鞋子)建議，不必列出裝備id，只列出裝備名稱)\n
    並將各部分明確分隔
    以下是可以參考的裝備庫:
    {item_description}

    請將文字控制在40行左右，並使用純文字格式，段落之間使用空白行隔開，每行不要超過50個字，不要使用Markdown語法
    """
    return ret
def gen_AI_coaching():
    try:
        prompt = gen_prompt()
        #print(prompt)
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            config=types.GenerateContentConfig(system_instruction="你是一個英雄聯盟的教練，目的是提供關於英雄聯盟的知識及攻略"),
            contents=prompt
        )
        if response.candidates:
                # 檢查是否有內容
                if response.candidates[0].content.parts:
                    return str(response.text)
                else:
                    return str(response.prompt_feedback)
        else:
            return "❌ 沒有產生任何結果，可能是安全機制攔截。"
    except Exception:
        return "未偵測到對局，請重新嘗試"

myUI = tk.Tk()
myUI.title("AI Gaming Coach")

window_width = myUI.winfo_screenwidth()    # 取得螢幕寬度
window_height = myUI.winfo_screenheight()  # 取得螢幕高度

width = 600
height = 1000
left = int((window_width - width)/2)       # 計算左上 x 座標
top = int((window_height - height)/2)      # 計算左上 y 座標
myUI.geometry(f'{width}x{height}+{left}+{top}')
myUI.resizable(True,True)

cnt = 1
coaching = tk.StringVar()
blue = tk.StringVar()
red = tk.StringVar()
def data_reset():
    if check_current_state():
        try:
            my_champion = "Akali"
            opponent_champion = "Ahri"
            if not testing:
                my_champion, opponent_champion = get_matchup_data()
            blue.set("我方英雄:"+my_champion)
            red.set("敵方英雄:"+opponent_champion)
            response = gen_AI_coaching()
            coaching.set(response)
        except Exception:
            myUI.after(1000, data_reset)
            coaching.set("正在生成資料...")
    else:
        myUI.after(1000, data_reset)
        coaching.set("目前無對局進行，正在重試")
        

reset_button = tk.Button(myUI, text="重整資料", anchor = "n", command = data_reset)
mylabel = tk.Label(myUI, text='以下是對局提示', font=('Arial',25,'bold'), anchor = "n")
myresult = tk.Label(myUI, textvariable = coaching, font=('Arial'), anchor = "n")
reset_button.pack()
mylabel.pack()
tk.Label(myUI, textvariable = blue, font=('Arial',20,'bold'), fg="#007FFF", anchor = "n").pack()
tk.Label(myUI, textvariable = red, font=('Arial',20,'bold'), fg="#FF0000", anchor = "n").pack()
myresult.pack()
myUI.after(1000, data_reset)
myUI.mainloop()