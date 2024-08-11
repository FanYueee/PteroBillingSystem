import json
import discord
from discord.ext import commands
import datetime
from datetime import date, datetime, timedelta
from pydactyl import PterodactylClient
from typing import Optional
import requests
import time as tm
import asyncio
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
client = commands.Bot(command_prefix='/', intents=intents)

# Pterodactyl API 設置
api = PterodactylClient('https://domain', '')

# 全域變數
admin_roleID = 965456249204387860
payment_notify_channel = 1130389739669819443
role_not_exist = str("The required role does not exist.")
no_permission_admin = str("You do not have permission to use this command. (Admin)")
no_permission_user = str("You do not have permission to use this command. (User)")
no_account = str("You have not registered an account yet")
mail_exist = str("This email does exist.")
mail_not_exist = str("This email does not exist.")
serverID_not_exist = str("This Server ID does not exist.")
loading = str("<a:loading:1108348027221065758> 正在處理中...")
successful = str("**成功**")


# 啟動資訊
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    time = datetime.now()
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(f'\n{time} 機器人啟動成功！ ')
    await daily_task()


# log 紀錄
async def log(info, result):
    time = datetime.now()
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(f'\n{info} 結果: {result}')
    webhook_url = "https://discord.com/api/webhooks/"
    webhook_data = {
        "content": f"{info} 結果: {result}",
        "username": "Bot Command Notify"
    }
    try:
        result = requests.post(webhook_url, json=webhook_data)
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{result}")
    except:
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


# 區域判斷
def judgearea(location):
    if location == "1":
        return "臺灣"
    elif location == "2":
        return "新加坡中階型"
    elif location == "3":
        return "新加坡基本型"


# 創建帳號
@client.slash_command(name='createaccount', description='【Admin】創建控制面板帳號')
async def createaccount(ctx, mail: str, username: str, discord_id: str):
    returnInfo = await check_perm(ctx.author.roles)
    command = f"{ctx.author.id} {ctx.author.name}#{ctx.author.discriminator} {ctx.command.name} {mail} {username} {discord_id}"
    await ctx.respond(loading)
    if returnInfo[0] == 4:
        await log(command, returnInfo[1])
        await ctx.respond(returnInfo[1])
    else:
        with open('data.json', 'r') as f:
            data = json.load(f)

        if mail in data:
            await log(command, mail_exist)
            await ctx.edit(mail_exist)

        else:
            data[mail] = [{"discord_id": discord_id}]
            with open('data.json', 'w') as f:
                json.dump(data, f)

            api_result = api.user.create_user(username, mail, username, username)
            user_list = api.user.list_users(mail)
            user_id = user_list[0]['attributes']['id']

            embed = discord.Embed(title="帳號創建成功！", description="煩請您查收電子郵件中的最新信件，應有一封帳號創建成功信件，__**請點擊該信件內的網址設定面板密碼**__。",
                                  color=discord.Color.green())
            embed.add_field(name="", value=f"電子郵箱：{mail}", inline=True)
            embed.add_field(name="", value=f"Discord ID：{discord_id}", inline=True)
            embed.add_field(name="", value=f"帳戶名稱：{username}", inline=True)
            embed.add_field(name="", value=f"帳戶ID：{user_id}", inline=True)
            time = datetime.now()
            embed.set_footer(text=f"現在日期: {time}")

            await log(command, api_result)
            await ctx.edit(content="", embed=embed)


# 新增伺服器到用戶當中
@client.slash_command(name='createserver', description='【Admin】創建新伺服器（C,G,G）')
async def createserver(ctx, mail: str, price: int, cpu: int, ram: int, disk: int, location: str):
    returnInfo = await check_perm(ctx.author.roles)
    command = f"{ctx.author.id} {ctx.author.name}#{ctx.author.discriminator} {ctx.command.name} {mail} {price} {cpu} {ram} {disk} {location}"
    await ctx.respond(loading)
    if returnInfo[0] == 4:
        await log(command, returnInfo[1])
        await ctx.respond(returnInfo[1])

    else:
        cpu_send = cpu * 100
        ram_send = ram * 1024
        disk_send = disk * 1024

        with open('data.json', 'r') as f:
            data = json.load(f)

        if mail not in data:
            await log(command, mail_not_exist)
            await ctx.edit(mail_not_exist)
            return

        if mail in data:
            records = data[mail]

            for record in records:
                if 'discord_id' in record:
                    discord_id = record['discord_id']
                    break
                else:
                    continue
                break

        user_list = api.user.list_users(mail)
        user_id = user_list[0]['attributes']['id']
        api_result = api.servers.create_server(name=mail, user_id=user_id, nest_id=6, egg_id=29, memory_limit=ram_send,
                                               swap_limit=0, backup_limit=0, cpu_limit=cpu_send, disk_limit=disk_send,
                                               location_ids=[location])

        if str(api_result) == str("<Response [201]>"):
            server_id = api_result.json()['attributes']['id']
            server_identifier = api_result.json()['attributes']['uuid']
            today = datetime.now().strftime('%Y-%m-%d')
            data[mail].append(
                {'server_id': server_id, 'date': today, 'price': price, 'cpu': cpu, 'ram': ram, 'disk': disk,
                 'location': location})

            with open('data.json', 'w') as f:
                json.dump(data, f)

            location_name = judgearea(location)

            embed = discord.Embed(title="伺服器創建成功！", description="現在您可以登入控制面板 __https://owo__ 管理伺服器。",
                                  color=discord.Color.green())
            embed.add_field(name="", value=f"電子郵箱：{mail}", inline=True)
            embed.add_field(name="", value=f"Discord ID：{discord_id}", inline=True)
            embed.add_field(name="", value=f"帳戶 ID：{user_id}", inline=True)
            embed.add_field(name="", value=f"伺服器 ID：{server_id}", inline=True)
            embed.add_field(name="", value=f"價格：{price}", inline=True)
            embed.add_field(name="", value=f"CPU 限制：{cpu_send} %", inline=True)
            embed.add_field(name="", value=f"記憶體限制：{ram} GB", inline=True)
            embed.add_field(name="", value=f"儲存空間限制：{disk} GB", inline=True)
            embed.add_field(name="", value=f"伺服器區域：{location_name}", inline=True)
            embed.add_field(name="", value=f"伺服器唯一辨識碼：{server_identifier}", inline=False)
            embed.set_footer(text=f"目前時間: {today}")

            await log(command, api_result)
            await ctx.edit(content=f"API 回應資訊：{api_result}", embed=embed)
        else:
            await log(command, api_result)
            await ctx.edit(api_result)


# 續約到伺服器當中
@client.slash_command(name='renewserver', description='【Admin】續約伺服器期限')
async def renewserver(ctx, server_id: int, day: int):
    returnInfo = await check_perm(ctx.author.roles)
    command = f"{ctx.author.id} {ctx.author.name}#{ctx.author.discriminator} {ctx.command.name} {server_id} {day}"
    await ctx.respond(loading)
    if returnInfo[0] == 4:
        await log(command, returnInfo[1])
        await ctx.respond(returnInfo[1])
    else:
        with open('data.json', 'r') as f:
            data = json.load(f)

        success = 0

        for email, server_data in data.items():
            for server in server_data:
                if "server_id" in server and server["server_id"] == server_id:
                    price = server["price"]
                    date = server["date"]

                    cpu = server["cpu"] * 100
                    ram = server["ram"]
                    disk = server["disk"]
                    location = server["location"]

                    location_name = judgearea(location)

                    date = datetime.strptime(date, "%Y-%m-%d")
                    date = date + timedelta(days=day)
                    date = date.strftime("%Y-%m-%d")
                    server["date"] = date
                    with open('data.json', 'w') as f:
                        json.dump(data, f)
                    discord_id = server_data[0]["discord_id"]
                    uuid = api.servers.get_server_info(server_id=server_id)['uuid']
                    user_id = api.servers.get_server_info(server_id=server_id)['user']

                    embed = discord.Embed(title="伺服器續約成功！", description=f"現在您可以繼續管理伺服器，到期日期更新為 **{date}**。",
                                          color=discord.Color.green())
                    embed.add_field(name="", value=f"電子郵箱：{email}", inline=True)
                    embed.add_field(name="", value=f"Discord ID：{discord_id}", inline=True)
                    embed.add_field(name="", value=f"帳戶 ID：{user_id}", inline=True)
                    embed.add_field(name="", value=f"伺服器 ID：{server_id}", inline=True)
                    embed.add_field(name="", value=f"價格：{price}", inline=True)
                    embed.add_field(name="", value=f"CPU 限制：{cpu} %", inline=True)
                    embed.add_field(name="", value=f"記憶體限制：{ram} GB", inline=True)
                    embed.add_field(name="", value=f"儲存空間限制：{disk} GB", inline=True)
                    embed.add_field(name="", value=f"伺服器區域：{location_name}", inline=True)
                    embed.add_field(name="", value=f"伺服器唯一辨識碼：{uuid}", inline=False)
                    embed.set_footer(text=f"到期日期: {date}")

                    await log(command, successful)
                    success = 1

                    await ctx.edit(embed=embed)
                    break
                else:
                    continue
                break
        else:
            if success != 1:
                await log(command, serverID_not_exist)
                await ctx.edit(serverID_not_exist)


# 顯示用戶所有資訊&伺服器
@client.slash_command(name='userinfo', description='【Customer】查詢帳戶資訊')
async def userinfo(ctx, mail: str):
    command = f"{ctx.author.id} {ctx.author.name}#{ctx.author.discriminator} {ctx.command.name} {mail}"
    await ctx.respond(loading)

    with open("data.json", "r") as f:
        data = json.load(f)

    try:
        author_id = ctx.author.id
        member = ctx.guild.get_member(author_id)
        if not member:
            member = []

    except:
        author_id = ctx.author.id
        member = []

    try:
        user_data = data[mail]
        discord_id = user_data[0]['discord_id']

        if any(str(role.id) == str(admin_roleID) for role in getattr(member, 'roles', [])) or str(author_id) == str(
                discord_id):

            try:
                user_data = data[mail]
                server_data = user_data[1:]
                embed = discord.Embed(title=f"{mail} 的所有伺服器資訊", color=discord.Color.gold())
                total_price = 0
                for server in server_data:
                    server_id = server['server_id']
                    date = server['date']
                    price = server['price']
                    total_price += price
                    cpu = server.get('cpu', None)
                    if cpu is not None:
                        cpu = cpu * 100
                    ram = server.get('ram', None)
                    disk = server.get('disk', None)
                    location = server.get('location', None)
                    identifier = api.servers.get_server_info(server_id=server_id)['identifier']

                    location_name = judgearea(location)

                    embed.add_field(name=f"伺服器 ID: {server_id}",
                                    value=f"到期日期: {date}\n價格: {price}\nCPU 限制: {cpu} %\nRAM 限制: {ram} GB\n儲存空間限制: {disk} GB\n伺服器位置: {location_name}\n伺服器唯一辨識碼: {identifier}",
                                    inline=True)

                embed.add_field(name=f"總金額 {total_price} 元", value="", inline=False)

                await log(command, successful)

                await ctx.edit(embed=embed)

            except KeyError:
                await log(command, mail_not_exist)
                await ctx.edit(mail_not_exist)
        else:
            command = f"{ctx.command.name} {mail}"
            await log(command, no_permission_user)
            await ctx.edit(no_permission_user)
    except:
        command = f"{ctx.command.name} {mail}"
        await log(command, no_account)
        await ctx.edit(no_account)


# 編輯伺服器資源量
@client.slash_command(name='editserver', description='【Admin】編輯伺服器資源量')
async def editserver(ctx, server_id: int, price: Optional[int] = None, cpu: Optional[int] = None,
                     ram: Optional[int] = None, disk: Optional[int] = None):
    returnInfo = await check_perm(ctx.author.roles)
    command = f"{ctx.author.id} {ctx.author.name}#{ctx.author.discriminator} {ctx.command.name} {server_id} {cpu} {ram} {disk}"
    await ctx.respond(loading)
    if returnInfo[0] == 4:
        await log(command, returnInfo[1])
        await ctx.respond(returnInfo[1])
    else:

        with open('data.json', 'r') as f:
            data = json.loads(f.read())

        api_result = 0

        for item in data.values():
            for server in item:
                if 'server_id' in server and server['server_id'] == server_id:
                    result = api.servers.get_server_info(server_id=server_id)
                    allocation_id = result['allocation']
                    io_limit = result['limits']['io']
                    database_limit = result['feature_limits']['databases']
                    allocation_limit = result['feature_limits']['allocations']
                    backup_limit = result['feature_limits']['backups']

                    if cpu is not None:
                        cpu = cpu * 100
                    else:
                        cpu = result['limits']['cpu']
                    if ram is not None:
                        ram = ram * 1024
                    else:
                        ram = result['limits']['memory']
                    if disk is not None:
                        disk = disk * 1024
                    else:
                        disk = result['limits']['disk']
                    if price is None:
                        price = server['price']

                    api_result = api.servers.update_server_build(server_id=server_id, allocation_id=allocation_id,
                                                                 memory_limit=ram, swap_limit=0, disk_limit=disk,
                                                                 cpu_limit=cpu, io_limit=io_limit,
                                                                 database_limit=database_limit,
                                                                 allocation_limit=allocation_limit,
                                                                 backup_limit=backup_limit, add_allocations=None,
                                                                 remove_allocations=None, oom_disabled=True)
                    break
            else:
                continue
            break

        if str(api_result) == str("<Response [200]>"):
            end = api.servers.get_server_info(server_id=server_id)
            ram = end['limits']['memory'] / 1024
            cpu = end['limits']['cpu'] / 100
            disk = end['limits']['disk'] / 1024

            for item in data.values():
                for server in item:
                    if 'server_id' in server and server['server_id'] == server_id:
                        server['price'] = int(price)
                        server['cpu'] = int(cpu)
                        server['ram'] = int(ram)
                        server['disk'] = int(disk)
                        break
                else:
                    continue
                break

            with open('data.json', 'w') as f:
                json.dump(data, f)

            for email, server_data in data.items():
                for server in server_data:
                    if "server_id" in server and server["server_id"] == server_id:
                        price = server["price"]
                        cpu_send = server["cpu"] * 100
                        ram = server["ram"]
                        disk = server["disk"]
                        location = server["location"]

                        location_name = judgearea(location)

                        server_date = server["date"]
                        discord_id = server_data[0]["discord_id"]
                        uuid = api.servers.get_server_info(server_id=server_id)['uuid']
                        user_id = api.servers.get_server_info(server_id=server_id)['user']

                        embed = discord.Embed(title="伺服器資源編輯成功！", description="請至伺服器控制面板確認資源。",
                                              color=discord.Color.green())
                        embed.add_field(name="", value=f"電子郵箱：{email}", inline=True)
                        embed.add_field(name="", value=f"Discord ID：{discord_id}", inline=True)
                        embed.add_field(name="", value=f"帳戶 ID：{user_id}", inline=True)
                        embed.add_field(name="", value=f"伺服器 ID：{server_id}", inline=True)
                        embed.add_field(name="", value=f"價格：{price}", inline=True)
                        embed.add_field(name="", value=f"CPU 限制：{cpu_send} %", inline=True)
                        embed.add_field(name="", value=f"記憶體限制：{ram} GB", inline=True)
                        embed.add_field(name="", value=f"儲存空間限制：{disk} GB", inline=True)
                        embed.add_field(name="", value=f"伺服器區域：{location_name}", inline=True)
                        embed.add_field(name="", value=f"伺服器唯一辨識碼：{uuid}", inline=False)
                        embed.set_footer(text=f"到期日期: {server_date}")

                        command = f"{ctx.command.name} {server_id} {cpu} {ram} {disk}"
                        await log(command, successful)

                        await ctx.edit(content=f"API 回應資訊：{api_result}", embed=embed)
                        break
        else:
            await log(command, api_result)
            await ctx.edit(serverID_not_exist)


# Get Server Info from Pterodactyl API
@client.slash_command(name='adminserverinfo', description='【Admin】Debug Get Server Info from Pterodactyl API')
async def adminserverinfo(ctx, server_id: int):
    returnInfo = await check_perm(ctx.author.roles)
    command = f"{ctx.author.id} {ctx.author.name}#{ctx.author.discriminator} {ctx.command.name} {server_id}"
    await ctx.respond(loading)
    if returnInfo[0] == 4:
        await log(command, returnInfo[1])
        await ctx.respond(returnInfo[1])
    else:
        try:
            result = api.servers.get_server_info(server_id=server_id)
            await log(command, returnInfo[1])
            await ctx.respond(result)
        except:
            await log(command, serverID_not_exist)
            await ctx.respond(serverID_not_exist)

# 刪除使用者的伺服器（確認按鈕）
class deleteconfirmation(discord.ui.View):
    def __init__(self, timeout: int = 180, server_id="", required_role_id="", **kwargs):
        self.server_id = server_id
        self.required_role_id = required_role_id
        super().__init__(timeout=timeout, **kwargs)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="> **__刪除請求已超時__**", view=self)

    @discord.ui.button(label="確認刪除", style=discord.ButtonStyle.danger)
    async def button_callback(self, button, interaction):

        roles = interaction.user.roles

        for role in roles:
            if role.id == admin_roleID:

                with open('data.json', 'r') as f:
                    data = json.load(f)

                for email, servers in data.items():
                    for server in servers:
                        if server.get('server_id') == self.server_id:
                            servers.remove(server)

                with open('data.json', 'w') as f:
                    json.dump(data, f)

                api_result = api.servers.delete_server(self.server_id, force=False)

                if str(api_result) == str("<Response [204]>"):
                    embed = discord.Embed(color=discord.Colour.red())
                    embed.add_field(name=f"伺服器已經刪除成功 (Server ID: {self.server_id})", value="", inline=False)

                    await log("按鈕: 確認刪除", "成功刪除")
                    await interaction.response.send_message(embed=embed)

                else:
                    await log("按鈕: 確認刪除", api_result)
                    await interaction.response.send_message(api_result)
                break
        else:
            await log("按鈕: 確認刪除", no_permission_admin)
            await interaction.response.send_message(no_permission_admin)
            return


# 刪除使用者的伺服器
@client.slash_command(name='deleteserver', description='【Admin】刪除伺服器')
async def deleteserver(ctx, server_id: int):
    command = f"{ctx.author.id} {ctx.author.name}#{ctx.author.discriminator} {ctx.command.name} {server_id}"
    await ctx.respond(loading)
    try:
        returnInfo = await check_perm(ctx.author.roles)
        if returnInfo[0] == 4:
            await log(command, returnInfo[1])
            await ctx.edit(returnInfo[1])
        else:
            with open('data.json', 'r') as f:
                data = json.loads(f.read())

            for email, servers in data.items():
                for server in servers:
                    if server.get("server_id") == server_id:
                        for sub_item in data[email]:
                            if "discord_id" in sub_item:
                                discord_id = sub_item["discord_id"]
                                break
                        price = server["price"]
                        cpu_show = server["cpu"] * 100
                        ram = server["ram"]
                        disk = server["disk"]
                        location = server["location"]

                        location_name = judgearea(location)

                        server_date = server["date"]
                        uuid = api.servers.get_server_info(server_id=server_id)['uuid']
                        user_id = api.servers.get_server_info(server_id=server_id)['user']
                        embed = discord.Embed(title="確定刪除伺服器嗎？", description="此為不可逆之操作，請謹慎操作。您有 5 秒鐘的時間可以選擇。",
                                              color=discord.Color.brand_red())
                        embed.add_field(name="", value=f"電子郵箱：{email}", inline=True)
                        embed.add_field(name="", value=f"Discord ID：{discord_id}", inline=True)
                        embed.add_field(name="", value=f"帳戶 ID：{user_id}", inline=True)
                        embed.add_field(name="", value=f"**__伺服器 ID：{server_id}__**", inline=True)
                        embed.add_field(name="", value=f"價格：{price}", inline=True)
                        embed.add_field(name="", value=f"CPU 限制：{cpu_show} %", inline=True)
                        embed.add_field(name="", value=f"記憶體限制：{ram} GB", inline=True)
                        embed.add_field(name="", value=f"儲存空間限制：{disk} GB", inline=True)
                        embed.add_field(name="", value=f"伺服器區域：{location_name}", inline=True)
                        embed.add_field(name="", value=f"伺服器唯一辨識碼：{uuid}", inline=False)
                        embed.set_footer(text=f"到期日期: {server_date}")
                        await log(command, "發送刪除確認按鈕")
                        required_role_id = admin_roleID
                        message = await ctx.edit(embed=embed)
                        view = deleteconfirmation(timeout=5, server_id=server_id, required_role_id=required_role_id)
                        view.message = message
                        await message.edit(view=view)
    except:
        await log(command, no_permission_admin)
        await ctx.edit(no_permission_admin)

# 計算一天
async def daily_task():
    now = datetime.now()
    current_hour = now.hour
    print(current_hour)
    if current_hour == 6:
        await time_notify()
        await asyncio.sleep(24 * 60 * 60)
        await daily_task()
    else:
        await asyncio.sleep(60)
        await daily_task()


# 帳單通知
async def time_notify():
    with open('data.json') as f:
        data = json.load(f)
    today = datetime.today().date()
    for email, servers in data.items():
        discord_id = None
        for info in servers:
            if 'discord_id' in info:
                discord_id = info['discord_id']
                try:
                    notify_status = info['notification']
                except:
                    notify_status = None
                print(notify_status)
                break

        if discord_id is not None:
            for server in servers:
                if 'server_id' in server and 'date' in server:
                    server_id = server['server_id']
                    price = server['price']
                    cpu_show = server['cpu'] * 100
                    ram = server['ram']
                    disk = server['disk']
                    location = server['location']
                    if location == "1":
                        location_name = "Taiwan"
                    else:
                        location_name = "N/A"

                    server_date = datetime.strptime(server['date'], '%Y-%m-%d').date()
                    diff_days = (server_date - today).days

                    if diff_days in [7, 3, 0]:
                        if notify_status == True:
                            try:
                                content = f'伺服器 {server_id} 還剩 {diff_days} 天到期！'
                                print(content)
                                print(discord_id)

                                uuid = api.servers.get_server_info(server_id=server_id)['uuid']
                                user_id = api.servers.get_server_info(server_id=server_id)['user']

                                if diff_days == 0:
                                    status = "今天"
                                else:
                                    status = f"{diff_days} 天後"

                                embed = discord.Embed(title=f"您好，這是 owo Cloud 服務到期通知，您有服務將於 {status} 到期",
                                                      description="請盡速繳納款項以免服務中斷。",
                                                      color=discord.Colour.brand_red())
                                embed.add_field(name="", value="繳費請至 <#965987665512103976> 開啟計費部門客服單，讓客服人員為您處理，謝謝。",
                                                inline=False)
                                embed.add_field(name="", value=f"電子郵箱：{email}", inline=True)
                                embed.add_field(name="", value=f"Discord ID：{discord_id}", inline=True)
                                embed.add_field(name="", value=f"帳戶 ID：{user_id}", inline=True)
                                embed.add_field(name="", value=f"**__伺服器 ID：{server_id}__**", inline=True)
                                embed.add_field(name="", value=f"價格：{price}", inline=True)
                                embed.add_field(name="", value=f"CPU 限制：{cpu_show} %", inline=True)
                                embed.add_field(name="", value=f"記憶體限制：{ram} GB", inline=True)
                                embed.add_field(name="", value=f"儲存空間限制：{disk} GB", inline=True)
                                embed.add_field(name="", value=f"伺服器區域：{location_name}", inline=True)
                                embed.add_field(name="", value=f"伺服器唯一辨識碼：{uuid}", inline=False)
                                embed.add_field(name="", value=f"服務到期日期: **__{server_date}__**", inline=False)
                                embed.set_footer(text=f"發送時間: {datetime.now()}")
                                user = await client.fetch_user(discord_id)

                                # log 發送到 invoice -3 自動停權
                                await user.send(embed=embed)
                                invoice_url = "https://discord.com/api/webhooks/"
                                invoice = {
                                    "content": f"`{datetime.now()}　{server_id} 即將於 {status} 到期，價格：{price} 到期日期：{server_date}` 所有者：<@{discord_id}>",
                                    "username": "owo Cloud 帳務處理系統－發送成功"
                                }
                                requests.post(invoice_url, json=invoice)

                            except:
                                invoice_url = "https://discord.com/api/webhooks/"
                                invoice = {
                                    "content": f"`{datetime.now()}　{server_id} 即將於 {status} 到期，價格：{price} 到期日期：{server_date}` 所有者：<@{discord_id}>",
                                    "username": "owo Cloud 帳務處理系統－發送錯誤"
                                }
                                requests.post(invoice_url, json=invoice)
                        else:
                            invoice_url = "https://discord.com/api/webhooks/"
                            invoice = {
                                "content": f"`{datetime.now()}　{server_id} 即將於  到期，價格：{price} 到期日期：{server_date}` 所有者：<@{discord_id}>",
                                "username": "owo Cloud 帳務處理系統－發送錯誤（沒有開啟通知）"
                            }
                            requests.post(invoice_url, json=invoice)

                        await asyncio.sleep(5)

                    if diff_days == -3:
                        if notify_status == True:
                            try:
                                uuid = api.servers.get_server_info(server_id=server_id)['uuid']
                                user_id = api.servers.get_server_info(server_id=server_id)['user']

                                embed = discord.Embed(
                                    title=f"您好，這是 owo Cloud 服務到期通知，您的服務已經暫停。",
                                    color=discord.Colour.brand_red())
                                embed.add_field(name="",
                                                value="請盡速繳納未繳納款項，請注意未繳款兩天後資料將刪除。",
                                                inline=False)
                                embed.add_field(name="", value=f"電子郵箱：{email}", inline=True)
                                embed.add_field(name="", value=f"Discord ID：{discord_id}", inline=True)
                                embed.add_field(name="", value=f"帳戶 ID：{user_id}", inline=True)
                                embed.add_field(name="", value=f"**__伺服器 ID：{server_id}__**", inline=True)
                                embed.add_field(name="", value=f"價格：{price}", inline=True)
                                embed.add_field(name="", value=f"CPU 限制：{cpu_show} %", inline=True)
                                embed.add_field(name="", value=f"記憶體限制：{ram} GB", inline=True)
                                embed.add_field(name="", value=f"儲存空間限制：{disk} GB", inline=True)
                                embed.add_field(name="", value=f"伺服器區域：{location_name}", inline=True)
                                embed.add_field(name="", value=f"伺服器唯一辨識碼：{uuid}", inline=False)
                                embed.add_field(name="", value=f"服務到期日期: **__{server_date}__**", inline=False)
                                embed.set_footer(text=f"發送時間: {datetime.now()}")
                                user = await client.fetch_user(discord_id)
                                await user.send(embed=embed)
                                invoice_url = "https://discord.com/api/webhooks/"
                                invoice = {
                                    "content": f"`{datetime.now()}　{server_id} 已經被暫停，價格：{price} 到期日期：{server_date}` 所有者：<@{discord_id}>",
                                    "username": "owo Cloud 帳務處理系統－發送成功（服務暫停）"
                                }
                                requests.post(invoice_url, json=invoice)
                            except:
                                invoice_url = "https://discord.com/api/webhooks/"
                                invoice = {
                                    "content": f"`{datetime.now()}　{server_id} 已經被暫停，價格：{price} 到期日期：{server_date}` 所有者：<@{discord_id}>",
                                    "username": "owo Cloud 帳務處理系統－發送失敗（服務暫停）"
                                }
                                requests.post(invoice_url, json=invoice)
                        else:
                            invoice_url = "https://discord.com/api/webhooks/"
                            invoice = {
                                "content": f"`{datetime.now()}　{server_id} 已經被暫停，價格：{price} 到期日期：{server_date}` 所有者：<@{discord_id}>",
                                "username": "owo Cloud 帳務處理系統－發送失敗（沒有開啟通知）（服務暫停）"
                            }
                            requests.post(invoice_url, json=invoice)
                        await asyncio.sleep(5)

    await asyncio.sleep(10)


client.run('owo')
