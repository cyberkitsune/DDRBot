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
    generic_eamuse_session = None
    task_created = False
    lastrun = None
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
        if not self.task_created:
            self.loop.create_task(self.monitor_task())
            self.task_created = True
            print("Created monitoring thread!")


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

    async def show_screenshots(self, message):
        if str(message.author.id) not in self.linked_eamuse:
            await message.channel.send("Your e-amusement account isn't linked! Use `%slink` to link your account." % self.command_prefix)
            await message.channel.send("Once linked, this command can post your in-game score screenshots to discord.")
            return

        eal = EALink(cookies=(self.linked_eamuse[str(message.author.id)][0], self.linked_eamuse[str(message.author.id)][1]))
        photos = eal.get_screenshot_list()
        if len(photos) == 0:
            await message.channel.send("You don't have any screenshots saved from the last day. Go out and get some scores!")
            return
        await message.channel.send("Fetching your last %i scores, please wait..." % len(photos))
        screenshot_files = []
        for photo in photos:
            data = eal.get_jpeg_data_for(photo['file_path'])
            screenshot_files.append(discord.File(io.BytesIO(data), '%s-%s.jpg' % ((photo['game_name'], photo['last_play_date']))))
        if len(screenshot_files) > 10:
            screenshot_files = divide_chunks(screenshot_files, 10)
            await message.channel.send("Your screenshots for the last 48h:")
            for fileset in screenshot_files:
                await message.channel.send(files=fileset)
        else:
            await message.channel.send("Your screenshots for the last 48h:", files=screenshot_files)


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




if __name__ == "__main__":
    bot = DDRBotClient(sys.argv[2])
    bot.run(sys.argv[1])
