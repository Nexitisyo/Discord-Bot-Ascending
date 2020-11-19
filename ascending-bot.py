from __future__ import print_function
import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import discord
from discord.ext import commands
import datetime
from datetime import date
import logging
import logging.config
import math
import uuid
import re

# If modifying these scopes, delete the file token.pickle.
TOKEN = ''
SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = ''
SHEET_RANGE = ''
alias_title = ['-Titel', '-titel', '-title', '-Title']
alias_description = ['-Beschreibung', '-desc',
                     '-beschreibung', '-description', '-Description']
alias_location = ['-ort', '-Ort', '-location',
                  '-Location', '-channel', '-Channel']
alias_start = ['-start', '-Start', '-beginn', '-Beginn', '-von', '-Von']
alias_end = ['-ende', '-Ende', '-Schluss',
             '-schluss', '-bis', '-Bis', '-end', '-End']
alias_char = ['char', 'character', 'Char',
              'Character', 'name', 'Name', 'CharacterName']
alias_fam = ['fam', 'Familie', 'familie', 'Familienname', 'familienname']
alias_class = ['class', 'Klasse', 'klasse', 'race']
alias_lvl = ['level', 'lvl', 'Level', 'Lvl']
alias_ap = ['ak', 'ap', 'Ap', 'Ak', 'aP', 'aK', 'AK', 'AP']
alias_aap = ['aap', 'awaap', 'awak', 'AwaAK', 'Aawaak',
             'Awaak', 'Awak', 'AAK', 'aak', 'awaak', 'AwaAk', 'AAP']
alias_dp = ['dp', 'DP', 'dP', 'Dp', 'vk', 'VK', 'vK', 'Vk']

bot = commands.Bot(command_prefix='!')
bot.remove_command("help")
now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
eventRoles = [
    'Ascending Offi',  # Offi
    'Ascending Member'  # Member
]
with open("bot.log", "a") as log:
    log.write(
        "\n" + str(datetime.datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S")) + " LOG-START\n")

logging.basicConfig(filename='bot.log', filemode='a',
                    format='%(name)s - %(levelname)s - %(message)s')
# -------------------------------------------------------------------------------------------------------------------- #
#                                  CHECK CREDENTIALS AND SET GLOBAL VARIABLES                                          #
# -------------------------------------------------------------------------------------------------------------------- #
print("Loading Google API...")
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

try:
    print("Setting service for calendar...")
    service_calendar = build('calendar', 'v3', credentials=creds)
except IOError as e:
    logging.error("Could not create service_calendar")

try:
    print("Setting service for sheet...")
    service_sheet = build('sheets', 'v4', credentials=creds)
except IOError as e:
    logging.error("Could not create service_calendar")

print("Check for group.json")
if os.path.exists('groups.json'):
    f_group = open("group.json", "r+")
    print("group.json exists")
else:
    print("group.json does not exist\nCreating group.json")
    with open("group.json", "w+") as f_group:
        f_group = open("group.json", "r+")
        print("created")
# -------------------------------------------------------------------------------------------------------------------- #
#                                                                                                                      #
# -------------------------------------------------------------------------------------------------------------------- #


@bot.event
async def on_ready():
    print(bot.user.name)
    print(bot.user.id)
    print('----------------')
    gear_channel = bot.get_channel(428280078112260096)
    await bot.change_presence(activity=discord.Game(name="Eventplanner für Ascending"), status=discord.Status.online)


@bot.event
async def on_message(message):
    if message.channel.id == 660885671728119829 and message.author.id != bot.user.id and message.content[0] == "[" \
            or message.channel.id == 617013322684039189 and message.author.id != bot.user.id and message.content[0] == "[":
        for it, role in enumerate(eventRoles[1:]):
            if role in eventRoles:  # authorized
                split_content = re.findall("\[([^[\]]*)\]", message.content)
                generate_id = uuid.uuid1()
                event_id = str(generate_id.int)
                event_id = event_id[:6]

                start = split_content[3] + ":00"
                start = datetime.datetime.strptime(start, "%d.%m.%Y %H:%M:%S")

                end = split_content[4] + ":00"
                end = datetime.datetime.strptime(end, "%d.%m.%Y %H:%M:%S")

                if ' ' in str(split_content[3]):
                    start = str.replace(str(start), ' ', 'T')
                if ' ' in str(split_content[4]):
                    end = str.replace(str(end), ' ', 'T')

                event = {
                    "id": event_id,
                    "summary": split_content[0],
                    "location": split_content[2],
                    "description": split_content[1],
                    "start": {
                        "dateTime": start,
                        "timeZone": "Europe/Berlin"
                    },
                    "end": {
                        "dateTime": end,
                        "timeZone": "Europe/Berlin"
                    },
                    "attendees": [
                        {"email": "ascendingbdo@gmail.com"}
                    ],
                    "reminders": {
                        "useDefault": "False",
                        "overrides": [
                            {"method": "email", "minutes": 1440},
                            {"method": "popup", "minutes": 120}
                        ]
                    }
                }
                check = service_calendar.events().insert(
                    calendarId='primary', body=event).execute()
                if not check:
                    await message.channel.send("Event konnte nicht hinzugefügt werden")
                else:
                    await message.channel.send("Event hinzugefügt")

    await bot.process_commands(message)


@bot.command(aliases=['e_del'])
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member')
async def e_delete(ctx, *args):
    service = service_calendar
    for it, item in enumerate(args):
        if item == "-all":
            page_token = None
            while True:
                events = service_calendar.events().list(
                    calendarId='primary', pageToken=page_token).execute()
                for event in events['items']:
                    service_calendar.events().delete(calendarId='primary',
                                                     eventId=event['id']).execute()
                    page_token = events.get('nextPageToken')
                if not page_token:
                    break

    try:
        service_calendar.events().delete(
            calendarId='primary', eventId=args[0]).execute()
    except IOError:
        ctx.channel.send("Etwas ist schief gelaufen. Ist die ID korrekt?")
        logging.error("Could not delete calendar-event. Wrong ID")


@bot.command(aliases=['e_u', 'e_up'])
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member')
async def e_update(ctx, *args):
    summary = ""
    description = ""
    location = ""
    start = ""
    end = ""
    event_id = ""

    for it, item in enumerate(args):
        if item in alias_title:
            summary = args[it + 1]
        if item in alias_description:
            description = args[it + 1]
        if item in alias_location:
            location = args[it + 1]
        if item in alias_start:
            start = args[it + 1]
        if item in alias_end:
            end = args[it + 1]
        if item == "-id":
            event_id = args[it + 1]

    event = service_calendar.events().get(
        calendarId='primary', eventId=event_id).execute()

    if len(summary) > 0:
        event['summary'] = summary
    if len(description) > 0:
        event['description'] = description
    if len(location) > 0:
        event['location'] = location
    if len(start) > 0:
        event['start'] = {
            "dateTime": start,
            "timeZone": "Europe/Berlin"
        }
    if len(end) > 0:
        event['end'] = {
            "dateTime": end,
            "timeZone": "Europe/Berlin"
        }

    service_calendar.events().update(calendarId='primary',
                                     eventId=event['id'], body=event).execute()


async def all_args_for_new_event(channel, summary, description, location, start, end):
    if len(summary) <= 0:
        await channel.send("ERROR: Titel ungültig!")
        return False
    if len(description) <= 0:
        await channel.send(
            "ERROR: Beschreibung ungültig! Beschreibungen die länger als ein Wort sind müssen mit \" \" gekennzeichnet werden!")
        return False
    if len(location) <= 0:
        await channel.send("ERROR: Channel ungültig!")
        return False
    if len(start) <= 0:
        await channel.send("ERROR: Startdatum/Zeit ungültig!")
        return False
    if len(end) <= 0:
        await channel.send("ERROR: Enddatum/Zeit ungültig!")
        return False
    return True


@bot.command()
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member')
async def e_new(ctx, *args):
    summary = ""
    description = ""
    location = ""
    start = ""
    end = ""
    timeZone = "Europe/Berlin"
    if len(args) != 12:
        await ctx.channel.send("ERROR: Zu wenige/viele Argumente!")
        return False
    else:
        for it, item in enumerate(args):
            if item in alias_title:
                summary = args[it + 1]
            if item in alias_description:
                description = args[it + 1]
            if item in alias_location:
                location = args[it + 1]
            if item in alias_start:
                date = args[it + 1]
                time = args[it + 2]
                start = date + " " + time + ":00"
                start = datetime.datetime.strptime(start, "%d.%m.%Y %H:%M:%S")

                if ' ' in str(start):
                    start = str.replace(str(start), ' ', 'T')
            if item in alias_end:
                date = args[it + 1]
                time = args[it + 2]
                end = date + " " + time + ":00"
                end = datetime.datetime.strptime(end, "%d.%m.%Y %H:%M:%S")

                if ' ' in str(end):
                    end = str.replace(str(end), ' ', 'T')

    if all_args_for_new_event(channel=ctx, summary=summary, location=location, description=description, start=start, end=end):
        generate_id = uuid.uuid1()
        event_id = str(generate_id.int)
        event_id = event_id[:6]
        event = {
            "id": event_id,
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start,
                "timeZone": timeZone
            },
            "end": {
                "dateTime": end,
                "timeZone": timeZone
            },
            "attendees": [
                {"email": ""}
            ],
            "reminders": {
                "useDefault": "False",
                "overrides": [
                    {"method": "email", "minutes": 1440},
                    {"method": "popup", "minutes": 120}
                ]
            }
        }
        service_calendar.events().insert(calendarId='primary', body=event).execute()
        await current_events(ctx.channel.id)


@bot.command()
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member')
async def sheet(ctx):
    gear_channel = bot.get_channel(428280078112260096)
    title = "Memberliste Ascending"
    user_thumb = ctx.author.avatar_url
    embed = discord.Embed(title=title,
                          url="",
                          description="<@!" + str(
                              ctx.author.id) + "> " + "Unten findest Du die aktuelle Memberliste mit Gearstand, Eventteilnahmen und "
                                                      "Payout-Tier ",
                          color=0x53006f,
                          timestamp=datetime.datetime.utcfromtimestamp(1584793336))
    icon_url = user_thumb
    embed.set_author(name="Sheetlink", icon_url="h")
    embed.set_thumbnail(url=icon_url)
    embed.add_field(name="Sheet:",
                    value="",
                    inline=True)
    embed.set_footer(
        text="Bei Fehlern, Fragen oder Vorschlägen bitte Nexitis#0829 anschreiben\n")
    await gear_channel.send(embed=embed)


async def all_stats(ctx, entry):
    if len(entry[0]) < 1:
        await ctx.channel.send("ERROR: Bitte an einen Administrator wenden (ID not found)")
        return False
    if len(entry[1]) < 1:
        await ctx.channel.send("ERROR: Familienname fehlt")
        return False
    if len(entry[2]) < 1:
        await ctx.channel.send("ERROR: Charactername fehlt")
        return False
    if len(entry[3]) < 1:
        await ctx.channel.send("ERROR: Klasse fehlt")
        return False
    if len(entry[4]) < 1:
        await ctx.channel.send("ERROR: Level fehlt")
        return False
    if len(entry[5]) < 1:
        await ctx.channel.send("ERROR: AP/AK fehlt")
        return False
    if len(entry[6]) < 1:
        await ctx.channel.send("ERROR: AAP/AAK fehlt")
        return False
    if len(entry[7]) < 1:
        await ctx.channel.send("ERROR: DP fehlt")
        return False
    return True


@bot.command()
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member')
async def help(ctx):
    gear_channel = bot.get_channel(428280078112260096)
    embed = discord.Embed(title="Help",
                          colour=0x53006f, url="https://discordapp.com",
                          description="Gearupdate:",
                          timestamp=datetime.datetime.utcfromtimestamp(1584793336))
    value_new_member = "```diff\n" \
                       "Neue Benutzer müssen einmal alles angeben um in der Member-Liste eingetragen zu werden.\n" \
                       "+ !update CharacterName:ARlSEN Familienname:Chizen Level:62 AK:267 AwaAK:268 DP:297 Klasse:Guardian```"
    value_existing_member = "```diff\n" \
                            "Zum aktualisieren der Werte kann man beliebig viele Argumente angeben.\n" \
                            "+ !update CharacterName:NichtMehrARlSEN ap:200 dp:310\n" \
                            "+ !update ap:285\n" \
                            "etc.\n```"
    value_variation = "```diff\n" \
                      "+Befehl:\n" \
                      "[!update, !u, !up, !gear, !g]\n" \
                      "+Charactername:\n" \
                      "[char, character, Char, Character, name, Name, CharacterName]\n" \
                      "+Familienname:\n" \
                      "[fam, Familie, familie, Familienname, familienname]\n+Klasse\n[class, Klasse, klasse, race]\n" \
                      "+Level:\n" \
                      "[level, lvl, Level, Lvl]\n" \
                      "+AP\n" \
                      "[ak, ap, Ap, Ak, aP, aK, AK, AP]\n" \
                      "+AAP:\n" \
                      "[aap, awaap, awak, AwaAK, Aawaak, Awaak, Awak, AAK, aak]\n" \
                      "+DP:\n" \
                      "[dp, DP, dP, Dp, vk, VK, vK, Vk]\n" \
                      "Jeder Parameter kann in beliebiger Reihenfolge angegeben werden\n```"
    embed.add_field(name="Für neue Member:",
                    value=value_new_member, inline=False)
    embed.add_field(name="Für bestehende Member:",
                    value=value_existing_member, inline=False)
    embed.add_field(name="Variationen", value=value_variation, inline=False)
    embed.set_footer(
        text="Bei Fehlern, Fragen oder Vorschlägen bitte Nexitis#0829 anschreiben\n")
    await gear_channel.send(embed=embed)


async def post_update(ctx, entry):
    gear_channel = bot.get_channel(428280078112260096)
    title = "Update für: " + ctx.author.display_name
    user_thumb = ctx.author.avatar_url
    post_date = str(datetime.datetime.now().strftime(
        '%d.%m.%Y %H:%M')) + " <@!" + str(ctx.author.id) + "> "
    embed = discord.Embed(title=title,
                          url="",
                          description=post_date,
                          color=0x53006f,
                          timestamp=datetime.datetime.utcfromtimestamp(1584793336))
    icon_url = user_thumb
    embed.set_author(name="Gearupdate", icon_url="")
    embed.set_thumbnail(url=icon_url)
    m_class = entry[3]
    embed.add_field(name=":regional_indicator_c: Klasse:",
                    value=m_class, inline=True)
    lvl = entry[4]
    embed.add_field(name=":arrow_double_up: Level:", value=lvl, inline=True)
    ap = entry[5]
    embed.add_field(name=":dagger: AP:", value=ap, inline=True)
    aap = entry[6]
    embed.add_field(name=":crossed_swords: AAP:", value=aap, inline=True)
    dp = entry[7]
    embed.add_field(name=":shield: DP:", value=dp, inline=True)
    gs = entry[8]
    embed.add_field(name=":chart_with_upwards_trend: GS:",
                    value=gs, inline=True)
    embed.add_field(name="Sheet:", value="",
                    inline=True)
    embed.set_footer(
        text="Bei Fehlern, Fragen oder Vorschlägen bitte Nexitis#0829 anschreiben\n")
    await gear_channel.send(embed=embed)


@bot.command(aliases=['g', 'up', 'u', 'gear'])
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member')
async def update(ctx, *args):
    gear_channel = bot.get_channel(428280078112260096)
    sheet = service_sheet.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=SHEET_RANGE).execute()
    values = result.get('values', [])
    member_id = ctx.author.id
    pos = -1
    found_id = False
    found_any_arg = False
    for row in values:
        pos = pos + 1
        for entry in row:
            if entry == str(member_id):
                updated_entry = row
                found_id = True
                for it, stat in enumerate(args):
                    stat = stat.split(":")
                    if stat[0] in alias_fam:
                        member_fam = stat[1]
                        updated_entry[1] = member_fam
                        found_any_arg = True
                    if stat[0] in alias_char:
                        member_char = stat[1]
                        updated_entry[2] = member_char
                        found_any_arg = True
                    if stat[0] in alias_class:
                        member_class = stat[1]
                        updated_entry[3] = member_class
                        found_any_arg = True
                    if stat[0] in alias_lvl:
                        member_lvl = stat[1]
                        updated_entry[4] = member_lvl
                        found_any_arg = True
                    if stat[0] in alias_ap:
                        if not stat[1].isdigit():
                            await gear_channel.send("ERROR: AP muss eine Zahl sein.")
                        member_ap = stat[1]
                        updated_entry[5] = member_ap
                        found_any_arg = True
                    if stat[0] in alias_aap:
                        if not stat[1].isdigit():
                            await gear_channel.send("ERROR: AAP muss eine Zahl sein.")
                        member_aap = stat[1]
                        updated_entry[6] = member_aap
                        found_any_arg = True
                    if stat[0] in alias_dp:
                        if not stat[1].isdigit():
                            await gear_channel.send("ERROR: DP muss eine Zahl sein.")
                        member_dp = stat[1]
                        updated_entry[7] = member_dp
                        found_any_arg = True
                if found_any_arg:
                    updated_entry[8] = \
                        math.floor(
                            ((int(updated_entry[5]) + int(updated_entry[6])) / 2 + int(updated_entry[7])))
                    updated_entry[9] = str(date.today())
                    values[pos] = updated_entry
                    await post_update(ctx, updated_entry)
                    body = {
                        'values': values
                    }
                    service_sheet.spreadsheets().values().update(spreadsheetId=SHEET_ID,
                                                                 range=SHEET_RANGE,
                                                                 valueInputOption='USER_ENTERED',
                                                                 body=body).execute()
                else:
                    await ctx.channel.send("ERROR: Fehlerhafte Argumente (Hast du alles richtig geschrieben?)")
    if not found_id:
        if len(args) < 7:
            await ctx.channel.send(
                "ERROR: Hast du alle Parameter angegeben? Zur Hilfe schau dir die angepinnten Nachrichten an.")
        new_entry = [
            str(ctx.author.id),
            '',  # fam
            '',  # char
            '',  # class
            '',  # lvl
            '',  # ap
            '',  # aap
            '',  # dp
            '',  # gs
            ''  # date
        ]
        for it, stat in enumerate(args):
            stat = stat.split(":")
            if stat[0] in alias_fam:
                member_fam = stat[1]
                new_entry[1] = member_fam
            if stat[0] in alias_char:
                member_char = stat[1]
                new_entry[2] = member_char
            if stat[0] in alias_class:
                member_class = stat[1]
                new_entry[3] = member_class
            if stat[0] in alias_lvl:
                member_lvl = stat[1]
                new_entry[4] = member_lvl
            if stat[0] in alias_ap:
                if not stat[1].isdigit():
                    await ctx.channel.send("ERROR: AP muss eine Zahl sein.")
                member_ap = stat[1]
                new_entry[5] = member_ap
            if stat[0] in alias_aap:
                if not stat[1].isdigit():
                    await ctx.channel.send("ERROR: AP muss eine Zahl sein.")
                member_aap = stat[1]
                new_entry[6] = member_aap
            if stat[0] in alias_dp:
                if not stat[1].isdigit():
                    await ctx.channel.send("ERROR: AP muss eine Zahl sein.")
                member_dp = stat[1]
                new_entry[7] = member_dp

        if await all_stats(ctx, new_entry):
            new_entry[8] = math.floor(
                ((int(new_entry[5]) + int(new_entry[6])) / 2 + int(new_entry[7])))
            new_entry[9] = str(date.today())
            values.append(new_entry)
            await post_update(ctx, new_entry)
            body = {
                'values': values
            }
            service_sheet.spreadsheets().values().update(spreadsheetId=SHEET_ID,
                                                         range=SHEET_RANGE,
                                                         valueInputOption='USER_ENTERED',
                                                         body=body).execute()


@bot.command(aliases=['del', 'delete', 'clear'])
@commands.has_any_role('@Admin', 'Ascending Offis', 'Server Booster')
async def purge(ctx, limit):
    await ctx.channel.purge(limit=int(limit))


@bot.command()
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member')
async def current_events(ctx):
    # post_date = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M'))
    current_month = date.today()
    embed = discord.Embed(title="Nächsten 10 Events: ",
                          url="" + str(current_month.month) +
                          "/1?sf=true&pli=1",
                          description="" +
                              str(current_month.month) + "/1?sf=true&pli=1",
                          color=0x53006f,
                          timestamp=datetime.datetime.utcfromtimestamp(1584793336))

    events_result = service_calendar.events().list(calendarId='primary', timeMin=now,
                                                   maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    prefix = '```markdown\n'
    suffix = '```'
    if not events:
        embed.add_field(name="Events: ", value="Es finden keine Events statt.")
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if ":" == start[-3:-2]:
                start = start[:-3] + start[-2:]
            start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
            start = datetime.datetime.strftime(start, "%d.%m.%Y %H:%M:%S")
            prefix = prefix + \
                ("[" + event['id'] + "]" +
                 "(" + event['summary'] + ")" + "<" + start + ">\n")
        value = prefix + suffix
        embed.add_field(name="Events: ", value=value)
    embed.set_footer(
        text="Bei Fehlern, Fragen oder Vorschlägen bitte Nexitis#0829 anschreiben")
    await ctx.channel.send(embed=embed)


@bot.command()
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member', 'Ascending Support')
async def who(ctx, channel, message_id):
    sheet = service_sheet.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID,
                                range="Member Management!A:C").execute()
    values = result.get('values', [])
    reaction_list = []
    channel = str(channel).strip('<#>')
    channel = bot.get_channel(int(channel))
    async for message in channel.history(limit=200):
        if message.id == int(message_id):  # Find message
            for reaction in message.reactions:
                tmp = [[reaction.emoji]]
                async for users in reaction.users():  # Which user reacted what
                    for item in values:  # Value of sheet
                        if str(users.id) in item:  # is user in sheet?
                            # if yes reformat to fam:char string
                            member_name = str(item[1]) + ":" + str(item[2])
                            # add each user that was found and reacted with the same emoji
                            tmp[0].append(member_name)
                reaction_list.append(tmp[0])  # add list of users that reacted
    sorted_list = []

    for element_r in reaction_list:
        element_r[0] = str(element_r[0])
        if "<" in element_r[0]:
            start = ':'
            end = ':'
            element_r[0] = ":" + (element_r[0].split(start)
                                  )[1].split(end)[0] + ":"
            element_r.sort(key=lambda liste: element_r[1:])
        else:
            element_r[0:].sort()
        sorted_list.append(element_r)
    if len(reaction_list) > 0:
        await post_who(ctx, sorted_list)


async def post_who(ctx, reaction_list):
    title = "Liste der Reaktionen:"
    paginator = commands.Paginator(prefix='```markdown\n', suffix='```')
    paginator.add_line(title)

    for element in reaction_list:
        paginator.add_line(element[0])
        for entry in element[1:]:
            fam = str(entry).split(":")
            paginator.add_line("[" + fam[0] + "]" + "(" + fam[1] + ")")

    for pages in paginator.pages:
        await ctx.channel.send(content=pages)


@bot.command()
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member', 'Ascending Support')
async def gruppe(ctx, *args):
    # What if too many events? Paginator?
    markdown_prefix = '```markdown\n'
    markdown_suffix = '```'
    message = markdown_prefix

    sheet = service_sheet.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID,
                                range="Member Management!A:C").execute()
    values = result.get('values', [])

    reaction = args[0]
    id = str(uuid.uuid1().int)[:4]
    participants = "1"
    max_participants = "5"
    date = args[1]
    leader = "Chizen"
    description = args[2]
    groups = {
        'reaction': reaction,
        'id': id,
        'participants': participants,
        'max_participants': max_participants,
        'leader': leader,
        'date': date
    }

    embed = discord.Embed(
        description="Reagiere unter dem Post um einer Gruppe beizutreten", type="test", color=0x53006f)
    embed.set_author(name="Gruppensuche", icon_url="")
    message = message + reaction + \
        "[" + id + "]" + "(" + participants + "/" + max_participants + ")" + \
        "<" + leader + " " + date + ">" + "\n" + description
    message = message + markdown_suffix
    embed.add_field(name="Gruppe #", value=message)

    embed.set_footer(
        text="Bei Fehlern, Fragen oder Vorschlägen bitte Nexitis#0829 anschreiben\n")
    await ctx.channel.send(embed=embed)


@bot.command()
@commands.has_any_role('@Admin', 'Ascending Offis', 'Ascending Member', 'Ascending Support')
async def sahnetorte(ctx):
    await bot.close()

bot.run(TOKEN)
