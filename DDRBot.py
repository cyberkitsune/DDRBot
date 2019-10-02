from typing import List, Any

import discord, sys, asyncio, datetime, io, os, json, traceback
from py573jp.EAGate import EAGate
from py573jp.DDRPage import DDRApi
from py573jp.EALink import EALink
from py573jp.Exceptions import EALinkException
from Misc import RepresentsInt
from DDRArcadeMonitor import DDRArcadeMonitor


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


class DDRBotClient(discord.Client):
    admin_users = []
    command_handlers = {}
    command_prefix = 'k!'
    reporting_channels = []
    monitoring_arcades: List[DDRArcadeMonitor] = []
    linked_eamuse = {}
    shown_screenshots = {}
    generic_eamuse_session = None
    task_created = False
    lastrun = None
    auto_task_created = False
    auto_users = {}
    add_autos = []
    remove_autos = []
    warned_auto_error = []
    warned_no_users = False

    def __init__(self, session_id):
        self.generic_eamuse_session = session_id
        self.command_handlers['help'] = self.help_command
        self.command_handlers['lookup'] = self.lookup_command
        self.command_handlers['search'] = self.search_command
        self.command_handlers['addreport'] = self.addreport_command
        self.command_handlers['link'] = self.link_command
        self.command_handlers['scores'] = self.show_screenshots
        self.monitoring_arcades.append(DDRArcadeMonitor(sys.argv[2]))
        super().__init__()

    async def on_ready(self):
        print("DDRBot is ready!")
        if os.path.exists("linked.json"):
            print("Loaded saved e-amusement accounts!")
            with open("linked.json", 'r') as f:
                self.linked_eamuse = json.load(f)
        if os.path.exists("shown.json"):
            print("Loaded shown history!")
            with open("shown.json", 'r') as f:
                self.shown_screenshots = json.load(f)
        if os.path.exists("auto.json"):
            print("Loaded automode users!")
            with open("auto.json", 'r') as f:
                self.auto_users = json.load(f)
        if not self.task_created:
            self.loop.create_task(self.monitor_task())
            self.task_created = True
            print("Created monitoring thread!")
        if not self.auto_task_created:
            self.loop.create_task(self.auto_task())
            self.auto_task_created = True

    async def on_message(self, message: discord.Message):
        if message.content.startswith(self.command_prefix):
            try:
                command_name = message.content.split(" ", 1)[0]
                command_name = command_name.split(self.command_prefix, 1)[1]
            except Exception:
                command_name = ""

            print("Got command:", command_name)
            if command_name in self.command_handlers:
                try:
                    await self.command_handlers[command_name](message)
                except EALinkException as ex:
                    if ex.jscontext is not None:
                        await message.channel.send("Oops! uwu an error occured running that e-amusement command.\nError Reason:```\n%s```\nError JSON```\n%s```" % (ex, ex.jscontext))
                    else:
                        await message.channel.send("Oops! uwu an error occured running that e-amusement command.\nError Reason:```\n%s```" % ex)
                except Exception as ex:
                    await message.channel.send("Oops! uwu an error occured running that command.\nTechnical Details of Error: ```\n%s```" % (traceback.format_exc()))
            else:
                await message.channel.send("Sorry! %s is not a command... try doing %shelp..." % (command_name, self.command_prefix))

    async def help_command(self, message):
        command_list = ', '.join(self.command_handlers.keys())
        await message.channel.send("You can run the following commands: %s" % command_list)

    async def lookup_command(self, message):
        args = message.content.split(" ")
        if len(args) < 2 or not RepresentsInt(args[1]):
            await message.channel.send("You didn't specify a valid DDR ID!")
            return
        ddrid = int(args[1])
        await message.channel.send("Looking up player with DDR-ID %i..." % ddrid)
        api = EAGate(self.generic_eamuse_session)
        ddr = DDRApi(api)

        player = ddr.lookup_rival(ddrid)
        if player is None:
            await message.channel.send("Hmm... I can't find that player!")
        else:
            await message.channel.send("```\n%s\t%i```" % (player.name, player.ddrid))

    async def search_command(self, message):
        args = message.content.split(" ",1)
        if len(args) < 2:
            await message.channel.send("You didn't specify a name to search")
            return
        name = args[1]
        await message.channel.send("Looking up players with names like %s..." % name)
        api = EAGate(self.generic_eamuse_session)
        ddr = DDRApi(api)

        players = ddr.lookup_rivals(name)
        if len(players) == 0:
            await message.channel.send("Unable to find a players with a name like %s..." % name)
        else:
            userlist = ''.join(["%s\t%i\n" % (x.name, x.ddrid) for x in players])
            user_message = "Found Users:\n```%s```" % userlist
            await message.channel.send(user_message)

    async def addreport_command(self, message):
        if message.channel not in self.reporting_channels:
            self.reporting_channels.append(message.channel)
            await message.channel.send("Added this channel to the reporting list!")
        else:
            await message.channel.send("This channel is already a reporting destination!")

    async def link_command(self, message):
        if not isinstance(message.channel, discord.DMChannel):
            if str(message.author.id) not in self.linked_eamuse:
                await message.channel.send("Your e-amusement account is not linked!")
                await message.channel.send("Use this command in a DM with me to link your e-amusement account! **Do not use this command in public**")
                await message.channel.send("Usage:\n```%slink [username] [password] [otp (optional)]```" % self.command_prefix)
            else:
                await message.channel.send("Your e-amusement account is linked!")
                await message.channel.send("Use this command in a DM with me to link a different e-amusement account!")
            return
        args = message.content.split(" ")
        if len(args) < 3:
            await message.channel.send("Usage:\n```%slink [username] [password] [otp (optional)]```" % self.command_prefix)
            return
        eal = EALink()
        if len(args) > 3:
            eal.login(args[1], args[2], args[3])
        else:
            eal.login(args[1], args[2])

        if eal.logged_in:
            self.linked_eamuse[str(message.author.id)] = [eal.cookies[0], eal.cookies[1]]
            await message.channel.send("Logged in!\nYour cookies (for debug):\n```aqbsess=%s aqblog=%s```" % eal.cookies)
            with open("linked.json", 'w') as f:
                json.dump(self.linked_eamuse, f)
        else:
            await message.channel.send("Unable to log in!")

    async def auto_command(self, message):
        args = message.content.split(" ")
        if len(args) < 2:
            if str(message.author.id) in self.auto_users:
                await message.channel.send("You are opted-in to automatic screenshot DMs.")
            else:
                await message.channel.send("You are not yet opted in to automatic screenshot DMs.")
            await message.channel.send("This command allows you to opt-in to having the bot send you your screenshots automatically in a DM.\n"
                                       "Usage:\n"
                                       "```%sauto (on | off)" % self.command_prefix)
            return

        if args[1] == 'on':
            if str(message.author.id) not in self.auto_users:
                self.add_autos.append(str(message.author.id))
                await message.channel.send("You have opted-in to automatic screenshots! You will be DM'd them around a minute after taking them.")
            else:
                await message.channel.send("You are already opted-in to automatic screenshots. Opt-out by running `%sauto off`" % self.command_prefix)
        elif args[1] == 'off':
            if str(message.author.id) in self.auto_users:
                self.remove_autos.append(str(message.author.id))
                await message.channel.send("You are now opted-out of automatic screenshots. Opt back in by running `%sauto on`" % self.command_prefix)
            else:
                await message.channel.send("You're not opted-in to automatic screenshots. Opt in by running `%sauto on`" % self.command_prefix)
        else:
            await message.channel.send("Invalid syntax.\nUsage:\n```%sauto (on | off)```" % self.command_prefix)

    async def show_screenshots(self, message):
        if str(message.author.id) not in self.linked_eamuse:
            await message.channel.send("Your e-amusement account isn't linked! Use `%slink` to link your account." % self.command_prefix)
            await message.channel.send("Once linked, this command can post your in-game score screenshots to discord.")
            return
        showAll = 'all' in message.content
        eal = EALink(cookies=(self.linked_eamuse[str(message.author.id)][0], self.linked_eamuse[str(message.author.id)][1]))
        photos = eal.get_screenshot_list()
        if len(photos) == 0:
            await message.channel.send("You don't have any screenshots saved from the last day. Go out and get some scores!")
            return
        if not showAll:
            if str(message.author.id) not in self.shown_screenshots:
                self.shown_screenshots[str(message.author.id)] = []
            newOnly = []
            for photo in photos:
                key = "%s%s" % (photo['game_name'], photo['last_play_date'])
                if key not in self.shown_screenshots[str(message.author.id)]:
                    # New screenshot
                    newOnly.append(photo)
                    self.shown_screenshots[str(message.author.id)].append(key)
                else:
                    continue
            if len(newOnly) > 0:
                photos = newOnly
            else:
                await message.channel.send("No new screenshots since the last time you ran `%sscores`"
                                           "\nIf you'd like to see all your screenshots again please run `%sscores all`"
                                           % (self.command_prefix, self.command_prefix))
                return

        await message.channel.send("Fetching %i new scores from e-amusement, please wait..." % len(photos))
        screenshot_files = []
        for photo in photos:
            data = eal.get_jpeg_data_for(photo['file_path'])
            screenshot_files.append(discord.File(io.BytesIO(data), '%s-%s.jpg' % ((photo['game_name'], photo['last_play_date']))))
        if len(screenshot_files) > 10:
            screenshot_files = divide_chunks(screenshot_files, 10)
            await message.channel.send("Your screenshots since last check:")
            for fileset in screenshot_files:
                await message.channel.send(files=fileset)
            with open("shown.json", 'w') as f:
                json.dump(self.shown_screenshots, f)
        else:
            await message.channel.send("Your screenshots since last check:", files=screenshot_files)
            with open("shown.json", 'w') as f:
                json.dump(self.shown_screenshots, f)

    async def monitor_task(self):
        if len(self.reporting_channels) == 0:
            await asyncio.sleep(60)
            self.loop.create_task(self.monitor_task())
            return
        for arcade in self.monitoring_arcades:
            new_users = []
            api = EAGate(arcade.api_key)
            ddr = DDRApi(api)
            current_users = ddr.fetch_recent_players()
            if len(current_users) == 0:
                if not self.warned_no_users:
                    print("No current users returned...")
                    for channel in self.reporting_channels:
                        await channel.send("Hey! There are no recent users... this could be a bug!!!")
                    self.warned_no_users = True
                continue
            else:
                if self.warned_no_users:
                    self.warned_no_users = False
            if len(arcade.recent_players) == 0:
                arcade.recent_players = current_users
                continue
            old_set = arcade.recent_players
            if old_set[0] != current_users[0]:
                new_users.append(current_users[0])
                if old_set[0] != current_users[1]:
                    new_users.append(current_users[1]) # for 2p

            elif old_set[0] == current_users[0] and old_set[1] != current_users[1]:
                new_users.append(current_users[0])
                new_users.append(current_users[1])

            arcade.recent_players = current_users

            if len(new_users) > 0:
                user_str = '\n'.join(['%s\t%i' % (x.name, x.ddrid) for x in new_users])
                n_message = "Just logged out:\n```%s```" % user_str
                print(n_message)
                if len(self.reporting_channels) > 0:
                    for channel in self.reporting_channels:
                        await channel.send(n_message)
        await asyncio.sleep(60)
        self.loop.create_task(self.monitor_task())

    async def auto_task(self):
        if len(self.add_autos) > 0:
            for user_id in self.add_autos:
                self.auto_users[user_id] = 0
            self.add_autos = []
            with open('auto.json', 'w') as f:
                json.dump(self.auto_users, f)

        if len(self.remove_autos) > 0:
            for user_id in self.remove_autos:
                if user_id in self.auto_users:
                    del self.auto_users[user_id]
            self.remove_autos = []
            with open('auto.json', 'w') as f:
                json.dump(self.auto_users, f)

        for user_id in self.auto_users:
            last_time = int(self.auto_users[user_id])
            # Fetch screenshots
            eal = None
            try:
                eal = EALink(cookies=(self.linked_eamuse[str(user_id)][0], self.linked_eamuse[str(user_id)][1]))
                photos = eal.get_screenshot_list()
            except Exception as ex:
                if user_id not in self.warned_auto_error:
                    print("Exception fetching photos for %s\n%s" % (user_id, ex))
                    self.warned_auto_error.append(user_id)
                photos = []
            else:
                if user_id in self.warned_auto_error:
                    self.warned_auto_error.remove(user_id)

            if len(photos > 0):
                photos = sorted(photos, key=lambda x: int(x['last_play_date']))  # Smallest first
                new_photos = []
                for photo in photos:
                    if int(photo['last_play_date']) > last_time:
                        new_photos.append(photo)
                        last_time = int(photo['last_play_date'])

                if len(new_photos) > 0:
                    self.auto_users[user_id] = last_time
                    user = self.get_user(user_id)
                    if user is None:
                        continue
                    channel = user.dm_channel
                    if channel is None:
                        await user.create_dm()
                        channel = user.dm_channel

                    screenshot_files = []
                    for photo in new_photos:
                        data = eal.get_jpeg_data_for(photo['file_path'])
                        screenshot_files.append(discord.File(io.BytesIO(data), '%s-%s.jpg' % ((photo['game_name'], photo['last_play_date']))))
                    if len(screenshot_files) > 10:
                        screenshot_files = divide_chunks(screenshot_files, 10)
                        for fileset in screenshot_files:
                            await channel.send(files=fileset)
                    else:
                        await channel.send(files=screenshot_files)
                    with open('auto.json', 'w') as f:
                        json.dump(self.auto_users, f)

        await asyncio.sleep(60)
        self.loop.create_task(self.auto_task())


if __name__ == "__main__":
    bot = DDRBotClient(sys.argv[2])
    bot.run(sys.argv[1])
