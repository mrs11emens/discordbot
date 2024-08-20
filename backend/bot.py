import discord
from discord.ext import commands
from dotenv import dotenv_values
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json

# загрузка токена из .env 
token = dotenv_values("../.env")["TOKEN"]

# интенты
intents = discord.Intents.default()
intents.guilds = True # список событий
intents.members = True  # список юзеров
intents.messages = True # список сообщений
intents.message_content = True  # содержимое сообщений


# ставим префикс бота
bot = commands.Bot(command_prefix='!', intents=intents)

# хранение подписанного канала
subscribed_channels = []
# языки
channel_languages = {}

@bot.event
async def on_ready():
    global subscribed_channels, channel_languages

    print(f'Мы вошли как {bot.user}')
    
    # загружаем подписанные каналы, если они есть
    try:
        with open('../json/subchan.json', 'r', encoding='utf-8') as channels_file:
            subscribed_channels = json.load(channels_file)
    except FileNotFoundError:
        subscribed_channels = []
        print('subchan.json file not found, initializing subscribed_channels as an empty list.')
    except json.JSONDecodeError:
        subscribed_channels = []
        print('Error decoding subchan.json, initializing subscribed_channels as an empty list.')

    # загружаем языки, установленные в каналах, если они есть
    try:
        with open('../json/langset.json', 'r', encoding='utf-8') as langset_file:
            channel_languages = json.load(langset_file)
    except FileNotFoundError:
        channel_languages = {}
        print('langset.json file not found, initializing channel_languages as an empty dictionary.')
    except json.JSONDecodeError:
        channel_languages = {}
        print('Error decoding langset.json, initializing channel_languages as an empty dictionary.')

    print(subscribed_channels)
    print(channel_languages)

# выбор языка
@bot.command()
async def language(ctx, lang):
    if lang.lower() not in ['english', 'russian']:
        await ctx.send('Invalid language choice. Please choose "english" or "russian".')
        return
    
    # устанавливаем язык
    channel_languages[ctx.channel.id] = lang.lower()
    if lang.lower() == 'english':
        await ctx.send('Bot language is chosen as English.')
    elif lang.lower() == 'russian':
        await ctx.send('Язык бота - русский.')
    # записываем в файл установленный язык
    with open('../json/langset.json', 'w', encoding='utf-8') as f:
        json.dump(channel_languages, f, ensure_ascii=False, indent=4)

# подписка канала, куда будет кидаться инфа о сервере
@bot.command()
async def subscribe(ctx):
    lang = channel_languages.get(ctx.channel.id, 'english')
    
    if ctx.channel.id not in subscribed_channels:
        subscribed_channels.append(ctx.channel.id)
        if lang == 'english':
            await ctx.send(f'{ctx.channel.name} is subscribed to server updates.')
        elif lang == 'russian':
            await ctx.send(f'{ctx.channel.name} подписан на обновления сервера.')
    else:
        if lang == 'english':
            await ctx.send(f'{ctx.channel.name} is already subscribed.')
        elif lang == 'russian':
            await ctx.send(f'{ctx.channel.name} уже подписан.')
    # записываем в файл подписанный канал
    with open('../json/subchan.json', 'w', encoding='utf-8') as f:
        json.dump(subscribed_channels, f, ensure_ascii=False, indent=4)

# инфо о сервере в хмл
@bot.command()
async def send_server_info(ctx):
    guild = ctx.guild
    
    # элемент хмл дока
    root = ET.Element("ServerInfo")
    
    # инфа о сервере
    ET.SubElement(root, "ServerName").text = guild.name
    ET.SubElement(root, "ServerID").text = str(guild.id)
    ET.SubElement(root, "MemberCount").text = str(guild.member_count)

    # информация о каналах
    channels_element = ET.SubElement(root, "Channels")
    for guild_channel in guild.channels:
        channel_element = ET.SubElement(channels_element, "Channel")
        ET.SubElement(channel_element, "ChannelName").text = guild_channel.name
        ET.SubElement(channel_element, "ChannelID").text = str(guild_channel.id)
        ET.SubElement(channel_element, "ChannelType").text = str(guild_channel.type)

        # инфа о сообщениях
        if isinstance(guild_channel, discord.TextChannel):
            messages_element = ET.SubElement(channel_element, "Messages")
            async for message in guild_channel.history():
                message_element = ET.SubElement(messages_element, "Message")
                ET.SubElement(message_element, "MessageID").text = str(message.id)
                ET.SubElement(message_element, "Author").text = str(message.author)
                ET.SubElement(message_element, "Content").text = message.content

    # инфа о ролях
    roles_element = ET.SubElement(root, "Roles")
    for role in guild.roles:
        role_element = ET.SubElement(roles_element, "Role")
        ET.SubElement(role_element, "RoleName").text = role.name
        ET.SubElement(role_element, "RoleID").text = str(role.id)
    
    # инфа об участниках
    members_element = ET.SubElement(root, "Members")
    for member in guild.members:
        member_element = ET.SubElement(members_element, "Member")
        ET.SubElement(member_element, "MemberName").text = member.name
        ET.SubElement(member_element, "MemberID").text = str(member.id)

    # форматирум хмл
    xml_data = ET.tostring(root, encoding="unicode")
    formatted_xml = minidom.parseString(xml_data).toprettyxml(indent="  ")

    # записываем
    servname = f"../xml/server_info_{guild.name}.xml"
    with open(servname, "w", encoding='utf-8') as f:
        f.write(formatted_xml)

    lang = channel_languages.get(ctx.channel.id, 'english')
    for channel_id in subscribed_channels:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(file=discord.File(servname))
        else:
            if lang == 'english':
                print(f"Unsuccess attempt to get channelID {channel_id}")
            else:
                print(f"Не удалось найти канал с ID {channel_id}")

                

# запуск бота
bot.run(token)


