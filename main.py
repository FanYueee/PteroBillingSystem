import json
import discord
from discord.ext import commands
import datetime
from pydactyl import PterodactylClient
from typing import Optional
import requests

intents = discord.Intents.default()
client = commands.Bot(command_prefix='/', intents=intents)

# Pterodactyl API 設置
api = PterodactylClient('', '')

# 全域變數
admin_roleID = 
webhook_url = ""
token = ""
role_not_exist = str("The required role does not exist.")
no_permission_admin = str("You do not have permission to use this command. (Admin)")
mail_exist = str("This email does exist.")
mail_not_exist = str("This email does not exist.")
serverID_not_exist = str("This Server ID does not exist.")


# 啟動資訊
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    time = datetime.datetime.now()
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(f'\n{time} 機器人啟動成功！ ')

# log 紀錄
async def log(author_id, author_name, author_discriminator, command, result):
    time = datetime.datetime.now()
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(
            f'\n{time} {author_id} {author_name}#{author_discriminator} 使用指令 {command} 結果: {result}')
    webhook_data = {
        "content": f"{time} {author_id} <@{author_id}> {author_name}#{author_discriminator} 使用指令 {command} 結果: {result}",
        "username": "Bot Command Notify"
    }

    result = requests.post(webhook_url, json=webhook_data)
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{result}")

# 管理員權限驗證(4=有問題,1=成功)
async def check_perm(author_roles):
    if author_roles is None:
        return 4, 'The required role does not exist.'
    if admin_roleID not in [role.id for role in author_roles]:
        return 4, 'You do not have permission to use this command. (Admin)'
    else:
        return 1, "Verification passed"

client.run(token)
