from typing import List, Any

import discord, sys, asyncio, datetime, io, os, json, traceback, random, aiohttp, urllib.parse
from py573jp.EAGate import EAGate
from py573jp.DDRPage import DDRApi
from py573jp.EALink import EALink
from py573jp.Exceptions import EALinkException, EALoginException
from Misc import RepresentsInt
from DDRArcadeMonitor import DDRArcadeMonitor
from asyncio import queues

if os.path.exists("DDR_GENIE_ON"):
    from DDRScoreDB import db, User, Score, IIDXScore, DBTaskWorkItem
    from DDRGenie.DDRDataTypes import DDRParsedData, DDRScreenshot
    from DDRGenie.IIDXDataTypes import IIDXParsedData, IIDXScreenshot
    db.connect()


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


def harvest_cover(ss, pd):
    """
    Harvests an album cover if it's needed.
    :type ss: DDRScreenshot
    :type pd: DDRParsedData
    """
    if os.path.exists("covers/"):
        if not os.path.exists("covers/%s.png" % pd.song_title.value.strip()):
            print("[CoverScrape] Harvesting for %s" % pd.song_title)
            ss.album_art.save("covers/%s.png" % pd.song_title.value.strip(), format='PNG')


def save_json(filename, obj):
    try:
        with open(filename, 'w') as f:
            json.dump(obj, f)
    except IOError as ex:
        print("[JSON] Exception occured saving %s!\n%s" % (filename, ex))
    else:
        print("[JSON] Saved %s successfully." % filename)


def archive_screenshot(userid, filename, data):
    if not os.path.exists("archive/%s/" % userid):
        os.makedirs("archive/%s/" % userid)

    if not os.path.exists("archive/%s/%s" % (userid, filename)):
        with open("archive/%s/%s" % (userid, filename), 'wb') as f:
            f.write(data)


def load_json(filename):
    try:
        with open(filename, 'r') as f:
            obj = json.load(f)
    except IOError as ex:
        print("[JSON] Exception occured loading %s!\n%s" % (filename, ex))
        return None
    else:
        print("[JSON] Loaded %s successfully." % filename)
        return obj


def get_emoji_for_fc(fc_text):
    if 'MFC' in fc_text:
        return '<:mfc:472191264796966926>'
    elif 'PFC' in fc_text:
        return '<:pfc:472191264402702347>'
    elif 'GFC' in fc_text:
        return '<:gfc:472191264830259201>'
    elif 'FC' in fc_text:
        return '<:fc:472191264453033984>'
    else:
        return ''


def generate_embed(score_data, score_player):
    """
    :type score_data: DDRParsedData
    """
    emb = discord.Embed()
    first_mode = score_data.chart_play_mode.value[0]
    if first_mode == "V":
        first_mode = 'S'

    total_notes = int(score_data.score_marv_count.value) + int(score_data.score_perfect_count.value) + int(score_data.score_great_count.value) + int(
        score_data.score_good_count.value) + int(score_data.score_miss_count.value)

    marv_percent = (int(score_data.score_marv_count.value) / total_notes) * 100
    perfect_percent = (int(score_data.score_perfect_count.value) / total_notes) * 100
    great_percent = (int(score_data.score_great_count.value) / total_notes) * 100
    good_percent = (int(score_data.score_good_count.value) / total_notes) * 100
    miss_percent = (int(score_data.score_miss_count.value) / total_notes) * 100

    emb.title = "<:ddr_arrow:687073061039505454> %s by %s (%s%sP %s)" % (score_data.song_title, score_data.song_artist, score_data.chart_difficulty.value[0],
                                     first_mode, score_data.chart_difficulty_number.value)
    emb.description = "Played by %s" % score_player
    emb.add_field(name="💯 Grade", value="%s %s" % (score_data.play_letter_grade, get_emoji_for_fc(score_data.play_full_combo)), inline=True)
    emb.add_field(name="📈 Score", value="%s" % score_data.play_money_score, inline=True)
    emb.add_field(name="🎯 EXScore", value="%s" % score_data.play_ex_score, inline=True)
    emb.add_field(name="🔢 Max Combo", value="%s" % score_data.play_max_combo, inline=True)
    emb.add_field(name="<:mfc:472191264796966926> Marvelous", value="%s (%0.2f%%)" % (score_data.score_marv_count, marv_percent), inline=True)
    emb.add_field(name="<:pfc:472191264402702347> Perfect", value="%s (%0.2f%%)" % (score_data.score_perfect_count, perfect_percent), inline=True)
    emb.add_field(name="<:gfc:472191264830259201> Great", value="%s (%0.2f%%)" % (score_data.score_great_count, great_percent), inline=True)
    emb.add_field(name="<:fc:472191264453033984> Good", value="%s (%0.2f%%)" % (score_data.score_good_count, good_percent), inline=True)
    emb.add_field(name="<:eming:572201816792629267> Miss", value="%s (%0.2f%%)" % (score_data.score_miss_count, miss_percent), inline=True)
    emb.add_field(name="<:emiok:572201794982248452> OK", value="%s" % score_data.score_OK_count, inline=True)
    emb.set_footer(text="DDR-Genie [β] - C: %i%%" % int(score_data.title_conf * 100))
    if os.path.exists("covers/%s.png" % score_data.song_title.value.strip()):
        emb.set_thumbnail(url="https://assets.cyberkitsune.net/ddr_cover/%s.png" % urllib.parse.quote(score_data.song_title.value.strip()))
    if score_data.date_time is not None:
        emb.timestamp = score_data.date_time
    return emb


def generate_embed_iidx(score_data, score_player):
    """
    :type score_data: IIDXParsedData
    """
    emb = discord.Embed()

    emb.title = "<:iidx:540794989316145162> %s by %s [%s %s]" % (score_data.song_title, score_data.song_artist, score_data.chart_play_mode,
                                      score_data.chart_difficulty)
    emb.description = "Played by %s" % score_player
    emb.add_field(name="🎉 Clear Type", value="%s" % score_data.play_clear_type, inline=True)
    emb.add_field(name="💯 DJ Level", value="%s" % score_data.play_dj_level, inline=True)
    emb.add_field(name="🎯 EXScore", value="%s" % score_data.play_ex_score, inline=True)
    emb.add_field(name="❌ Miss Count", value="%s" % score_data.play_miss_count, inline=True)
    emb.add_field(name="🌈 PGreat", value="%s" % score_data.score_rainbow_count, inline=True)
    emb.add_field(name="👍 Great", value="%s" % score_data.score_great_count, inline=True)
    emb.add_field(name="😐 Good", value="%s" % score_data.score_good_count, inline=True)
    emb.add_field(name="👎 Bad", value="%s" % score_data.score_bad_count, inline=True)
    emb.add_field(name="🆖 Poor", value="%s" % score_data.score_poor_count, inline=True)
    emb.add_field(name="⛓ Combo Break", value="%s" % score_data.score_combo_break, inline=True)
    emb.add_field(name="🥕 Fast", value="%s" % score_data.score_fast_count, inline=True)
    emb.add_field(name="🐢 Slow", value="%s" % score_data.score_slow_count, inline=True)
    emb.set_footer(text="IIDX-Genie [α] - C: %i%%" % int(score_data.overall_conf))
    if score_data.date_time is not None:
        emb.timestamp = score_data.date_time
    return emb


def generate_embed_iidx_db(score_data, score_player, verified=False, cmd_prefix='k!'):
    """
    :type score_data: IIDXScore
    """
    if verified:
        v = '<:verified:680629672735670352>'
    else:
        v = ''

    emb = discord.Embed()

    emb.title = "<:iidx:540794989316145162> %s by %s [%s %s]" % (score_data.song_title, score_data.song_artist,
                                      'DP' if score_data.double_play else 'SP', score_data.difficulty)
    emb.description = "Played by %s %s\nView Screenshot `%sscreenshot iidx%i`" % (score_player, v, cmd_prefix, score_data.id)
    emb.add_field(name="🎉 Clear Type", value="%s" % score_data.clear_type, inline=True)
    emb.add_field(name="💯 DJ Level", value="%s" % score_data.dj_grade, inline=True)
    emb.add_field(name="🎯 EXScore", value="%s" % score_data.ex_score, inline=True)
    emb.add_field(name="❌ Miss Count", value="%s" % score_data.miss_count, inline=True)
    emb.add_field(name="🌈 PGreat", value="%s" % score_data.p_great_count, inline=True)
    emb.add_field(name="👍 Great", value="%s" % score_data.great_count, inline=True)
    emb.add_field(name="😐 Good", value="%s" % score_data.good_count, inline=True)
    emb.add_field(name="👎 Bad", value="%s" % score_data.bad_count, inline=True)
    emb.add_field(name="🆖 Poor", value="%s" % score_data.poor_count, inline=True)
    emb.add_field(name="⛓ Combo Break", value="%s" % score_data.combo_break, inline=True)
    emb.add_field(name="🥕 Fast", value="%s" % score_data.fast_count, inline=True)
    emb.add_field(name="🐢 Slow", value="%s" % score_data.slow_count, inline=True)
    emb.set_footer(text="IIDX-Genie [α] - C: %i%% ID: iidx%i" % (int(score_data.overall_confidence), score_data.id))
    if score_data.recorded_time is not None:
        emb.timestamp = score_data.recorded_time
    return emb


def generate_embed_from_db(score_data, score_player, verified=False, cmd_prefix='k!'):
    """
    :type score_data: Score
    """
    if isinstance(score_data, IIDXScore):
        return generate_embed_iidx_db(score_data, score_player, verified, cmd_prefix)
    emb = discord.Embed()
    if score_data.doubles_play:
        first_mode = 'D'
    else:
        first_mode = 'S'
    if verified:
        v = '<:verified:680629672735670352>'
    else:
        v = ''

    total_notes = int(score_data.marv_count) + int(score_data.perf_count) + int(score_data.great_count) + \
                  int(score_data.good_count) + int(score_data.miss_count)

    marv_percent = (int(score_data.marv_count) / total_notes)*100
    perfect_percent = (int(score_data.perf_count) / total_notes) * 100
    great_percent = (int(score_data.great_count) / total_notes) * 100
    good_percent = (int(score_data.good_count) / total_notes) * 100
    miss_percent = (int(score_data.miss_count) / total_notes) * 100

    emb.title = "<:ddr_arrow:687073061039505454> %s by %s (%s%sP %s)" % (score_data.song_title, score_data.song_artist, score_data.difficulty_name[0],
                                     first_mode, score_data.difficulty_number)
    emb.description = "Played by %s %s\nView Screenshot `%sscreenshot %i`" % (score_player, v, cmd_prefix, score_data.id)
    emb.add_field(name="💯 Grade", value="%s %s" % (score_data.letter_grade, get_emoji_for_fc(score_data.full_combo)), inline=True)
    emb.add_field(name="📈 Score", value="%s" % score_data.money_score, inline=True)
    emb.add_field(name="🎯 EXScore", value="%s" % score_data.ex_score, inline=True)
    emb.add_field(name="🔢 Max Combo", value="%s" % score_data.max_combo, inline=True)
    emb.add_field(name="<:mfc:472191264796966926> Marvelous", value="%s (%0.2f%%)" % (score_data.marv_count, marv_percent), inline=True)
    emb.add_field(name="<:pfc:472191264402702347> Perfect", value="%s (%0.2f%%)" % (score_data.perf_count, perfect_percent), inline=True)
    emb.add_field(name="<:gfc:472191264830259201> Great", value="%s (%0.2f%%)" % (score_data.great_count, great_percent), inline=True)
    emb.add_field(name="<:fc:472191264453033984> Good", value="%s (%0.2f%%)" % (score_data.good_count, good_percent), inline=True)
    emb.add_field(name="<:eming:572201816792629267> Miss", value="%s (%0.2f%%)" % (score_data.miss_count, miss_percent), inline=True)
    emb.add_field(name="<:emiok:572201794982248452> OK", value="%s" % score_data.OK_count, inline=True)
    emb.set_footer(text="DDR-Genie [β] - C: %i%% ID: %i" % (int(score_data.name_confidence * 100), score_data.id))
    emb.timestamp = score_data.recorded_time
    if os.path.exists("covers/%s.png" % score_data.song_title.strip()):
        emb.set_thumbnail(url="https://assets.cyberkitsune.net/ddr_cover/%s.png" % urllib.parse.quote(score_data.song_title.strip()))
    return emb


class YeetException(Exception):
    pass


class DDRBotClient(discord.Client):
    admin_users = ['109500246106587136']
    command_handlers = {}
    command_prefix = 'k!'
    authorized_channels = {}
    monitoring_arcades: List[DDRArcadeMonitor] = []
    linked_eamuse = {}
    shown_screenshots = {}
    memes = {}
    generic_eamuse_session = None
    task_created = False
    lastrun = None
    auto_task_created = False
    auto_users = {}
    add_autos = []
    remove_autos = []
    warned_auto_error = []
    warned_no_users = False

    db_add_queue = queues.Queue()
    db_task_started = False

    feed_task_created = False
    new_scores = queues.Queue()

    def __init__(self, session_id):
        self.generic_eamuse_session = session_id
        self.command_handlers['help'] = self.help_command
        self.command_handlers['lookup'] = self.lookup_command
        self.command_handlers['search'] = self.search_command
        self.command_handlers['addreport'] = self.addreport_command
        self.command_handlers['link'] = self.link_command
        self.command_handlers['scores'] = self.show_screenshots
        self.command_handlers['auto'] = self.auto_command
        self.command_handlers['authorize'] = self.auth_channel
        self.command_handlers['yeet'] = self.yeet
        if os.path.exists("ENABLE_SHITPOST"):
            self.command_handlers['meme'] = self.meme_manage
            self.command_handlers['memeon'] = self.shitpost_authorize
        if os.path.exists("DDR_GENIE_ON"):
            self.command_handlers['genie'] = self.genie_command
            self.command_handlers['top'] = self.top_scores
            self.command_handlers['setfeed'] = self.feed_authorize
            self.command_handlers['screenshot'] = self.fetch_screenshot
            self.command_handlers['show'] = self.show_score
            self.command_handlers['redo'] = self.requeue_db
            self.command_handlers['manual'] = self.manual_db
            self.command_handlers['leaderboard'] = self.bot_leaderboard
            self.command_handlers['csv'] = self.csv_command
            #self.command_handlers['pb'] = self.list_pb

        self.monitoring_arcades.append(DDRArcadeMonitor(sys.argv[2]))
        self.deep_ai = None
        super().__init__()

    async def on_ready(self):
        print("[BOT] DDRBot is ready!")
        if os.path.exists("linked.json"):
            print("[BOT] Loading saved e-amusement accounts!")
            self.linked_eamuse = load_json("linked.json")
        if os.path.exists("shown.json"):
            print("[BOT] Loading shown history!")
            self.shown_screenshots = load_json("shown.json")
        if os.path.exists("auto.json"):
            print("[BOT] Loading automode users!")
            self.auto_users = load_json("auto.json")
        if os.path.exists("channels.json"):
            print("[BOT] Loading authorized channels!")
            self.authorized_channels = load_json("channels.json")
        if os.path.exists("memes.json"):
            print("[BOT] Loaded memes!")
            self.memes = load_json("memes.json")
        if not self.task_created:
            self.loop.create_task(self.monitor_task())
            self.task_created = True
            print("[TASK] Created monitoring thread!")
        if not self.auto_task_created:
            self.loop.create_task(self.auto_task())
            self.auto_task_created = True
            print("[TASK] Created auto thread")
        if not self.db_task_started:
            self.loop.create_task(self.db_task())
            self.db_task_started = True
            print("[TASK] Created DB task")
        if not self.feed_task_created:
            self.loop.create_task(self.feed_task())
            self.feed_task_created = True
            print("[TASK] Created Feed task")
        if os.path.exists("deepai_key.txt"):
            print("[DEEPAI] DeepAI Key Exists. Enabling AI upscaling.")
            with open("deepai_key.txt", 'r') as f:
                self.deep_ai = f.read()
        else:
            self.deep_ai = None

    async def on_message(self, message: discord.Message):
        if 'commands' not in self.authorized_channels:
            self.authorized_channels['commands'] = []
        should_listen = str(message.author.id) in self.admin_users or str(message.channel.id) in self.authorized_channels['commands']
        if not should_listen:
            if isinstance(message.channel, discord.DMChannel):
                should_listen = True
            else:
                if str(message.author.id) == str(message.channel.guild.owner_id):
                    should_listen = True
        do_command = message.content.startswith(self.command_prefix)
        if should_listen:
            if do_command:
                try:
                    command_name = message.content.split(" ", 1)[0]
                    command_name = command_name.split(self.command_prefix, 1)[1]
                except Exception:
                    command_name = ""

                print("[CMD] %s#%s is running command %s" % (message.author.name, message.author.discriminator, command_name))
                if command_name in self.command_handlers:
                    try:
                        await self.command_handlers[command_name](message)
                    except EALinkException as ex:
                        if ex.jscontext is not None:
                            await message.channel.send("Oops! uwu an error occured running that e-amusement command.\nError Reason:```\n%s```\nError JSON```\n%s```" % (ex, ex.jscontext))
                        else:
                            await message.channel.send("Oops! uwu an error occured running that e-amusement command.\nError Reason:```\n%s```" % ex)
                    except YeetException as ex:
                        print("[YEET] YEEEET")
                        await self.logout()
                        if db is not None:
                            db.close()
                        await self.close()
                    except Exception as ex:
                        await message.channel.send("Oops! uwu an error occured running that command.\nTechnical Details of Error: ```\n%s```" % (traceback.format_exc()))
                elif os.path.exists("ENABLE_SHITPOST") and command_name in self.memes:
                    await self.run_meme(message, command_name)
                else:
                    await message.channel.send("Sorry! %s is not a command... try doing %shelp..." % (command_name, self.command_prefix))
        elif do_command and not should_listen:
            await message.channel.send("Sorry! I can't run commands in this channel. Ask a bot admin or the server owner to run %sauthorize in here." % self.command_prefix)

    async def meme_manage(self, message):
        can_add = str(message.author.id) in self.admin_users
        if can_add:
            args = message.content.split(" ")
            if len(args) < 2:
                await message.channel.send("Invalid Syntax! \nUsage:\n"
                                           "```%smeme add <meme name> <string>\n%smeme del <meme name> [string]```" % (self.command_prefix, self.command_prefix))
                return
            cmdlet = args[1]
            if args[1] == "add":
                if len(args) < 3:
                    await message.channel.send("Invalid Syntax! \nUsage:\n"
                                               "```%smeme add <meme name> <string>\n%smeme del <meme name> [string]```" % (
                                               self.command_prefix, self.command_prefix))
                    return
                name = args[2]
                if name not in self.memes:
                    self.memes[name] = []

                self.memes[name].append(' '.join(args[3:]))
                print("[MEME] Added new meme %s %s" % (name, ' '.join(args[3:])))
                await message.channel.send("Added meme!")
                save_json("memes.json", self.memes)

            elif args[1] == "del":
                name = args[2]
                if name not in self.memes:
                    await message.channel.send("%s isn't a meme yet! Can't delete!" % name)
                    return
                if len(args) > 3:
                    msg = ' '.join(args[3:])
                    if msg in self.memes[name]:
                        self.memes[name].remove(msg)
                        await message.channel.send("Deleted %s from %s" % (msg, name))
                        print("[MEME] Deleted %s from %s" % (msg, name))
                        save_json("memes.json", self.memes)
                    else:
                        await message.channel.send("%s doesn't have message %s..." % (name, msg))
                else:
                    if name in self.memes:
                        del self.memes[name]
                        await message.channel.send("Deleted %s from memes." % (name))
                        print("[MEME] Deleted %s from memes." % (name))
                        save_json("memes.json", self.memes)
            else:
                await message.channel.send("Invalid Syntax! \nUsage:\n"
                                           "```%smeme add <meme name> <string>\n%smeme del <meme name> [string]```" % (
                                           self.command_prefix, self.command_prefix))
                return
        else:
            await message.add_reaction('<:eming:572201816792629267>')

    async def run_meme(self, message, meme_name):
        if self.check_shitpost(message):
            string = random.choice(self.memes[meme_name])
            await message.channel.send(string)
        else:
            if str(message.guild.id) == str('572200197124390922') and str(message.author.id) == str('303023183924166661'):
                await message.delete()
            else:
                await message.add_reaction('<:eming:572201816792629267>')

    async def yeet(self, message):
        can_yeet = str(message.author.id) in self.admin_users
        if can_yeet:
            raise YeetException("YEET")
        else:
            await message.add_reaction('<:eming:572201816792629267>')

    def check_shitpost(self, message):
        if isinstance(message.channel, discord.DMChannel):
            return True

        if 'memes' in self.authorized_channels:
            return (str(message.channel.id) in self.authorized_channels['memes'])
        else:
            return False

    async def auth_channel(self, message):
        if not isinstance(message.channel, discord.TextChannel):
            await message.channel.send("Sorry, you can't run this in a DM.")
            return

        can_auth = message.author.id == message.channel.guild.owner_id
        if not can_auth:
            can_auth = str(message.author.id) in self.admin_users

        if not can_auth:
            await message.channel.send("Sorry, only bot admins or guild owners can authorize channels.")
            return

        if 'commands' not in self.authorized_channels:
            self.authorized_channels['commands'] = []

        if str(message.channel.id) in self.authorized_channels['commands']:
            await message.channel.send("This channel is already authorized to run commands.\nRemoving authorization now.")
            self.authorized_channels['commands'].remove(str(message.channel.id))
        else:
            await message.channel.send("Authorized this channel to use commands!")
            self.authorized_channels['commands'].append(str(message.channel.id))

        save_json("channels.json", self.authorized_channels)

    async def shitpost_authorize(self, message):
        if not isinstance(message.channel, discord.TextChannel):
            await message.channel.send("Sorry, you can't run this in a DM.")
            return

        can_auth = message.author.id == message.channel.guild.owner_id
        if not can_auth:
            can_auth = str(message.author.id) in self.admin_users

        if not can_auth:
            await message.channel.send("Sorry, only bot admins or guild owners can authorize meme channels.")
            return

        if 'memes' not in self.authorized_channels:
            self.authorized_channels['memes'] = []

        if str(message.channel.id) in self.authorized_channels['memes']:
            await message.channel.send(
                "This channel is already authorized to run memes.\nRemoving authorization now.")
            self.authorized_channels['memes'].remove(str(message.channel.id))
        else:
            await message.channel.send("Authorized this channel to use memes!")
            self.authorized_channels['memes'].append(str(message.channel.id))

        save_json("channels.json", self.authorized_channels)

    async def feed_authorize(self, message):
        if not isinstance(message.channel, discord.TextChannel):
            await message.channel.send("Sorry, you can't run this in a DM.")
            return

        can_auth = message.author.id == message.channel.guild.owner_id
        if not can_auth:
            can_auth = str(message.author.id) in self.admin_users

        if not can_auth:
            await message.channel.send("Sorry, only bot admins or guild owners can authorize feed channels.")
            return

        if 'feed' not in self.authorized_channels:
            self.authorized_channels['feed'] = []

        if str(message.channel.id) in self.authorized_channels['feed']:
            await message.channel.send(
                "This channel is already a score feed.\nRemoving.")
            self.authorized_channels['feed'].remove(str(message.channel.id))
        else:
            await message.channel.send("Designated channel as score feed!")
            self.authorized_channels['feed'].append(str(message.channel.id))

        save_json("channels.json", self.authorized_channels)

    async def fetch_screenshot(self, message):
        args = message.content.split(' ')
        if len(args) < 2:
            await message.channel.send("Usage: `%sscreenshot [screenshot_id]`" % self.command_prefix)
            return

        st = Score
        if 'iidx' in args[1]:
            st = IIDXScore
            args[1] = args[1].strip('iidx')

        if not RepresentsInt(args[1]):
            await message.channel.send("`%s` is not a number!\n"
                                        "Usage: `%sscreenshot [screenshot_id]`" % (args[1], self.command_prefix))
            return

        s = st.get_or_none(id=args[1])
        if s is None:
            await message.channel.send("I can't find a screenshot with ID `%s`" % args[1])
            return

        if os.path.exists("archive/%s/%s" % (s.user.id, s.file_name)):
            await message.channel.send(file=discord.File("archive/%s/%s" % (s.user.id, s.file_name)))
        else:
            await message.channel.send("Weird, I don't have the screenshot file for that score recorded! 😦")

    async def show_score(self, message):
        args = message.content.split(' ')
        if len(args) < 2:
            await message.channel.send("Usage: `%sscore [score_id]`" % self.command_prefix)
            return

        st = Score
        if 'iidx' in args[1]:
            st = IIDXScore
            args[1] = args[1].strip('iidx')

        if not RepresentsInt(args[1]):
            await message.channel.send("`%s` is not a number!\n"
                                        "Usage: `%sscore [screenshot_id]`" % (args[1], self.command_prefix))
            return

        s = st.get_or_none(id=args[1])
        if s is None:
            await message.channel.send("I can't find a score with ID `%s`" % args[1])
            return

        await message.channel.send(embed=generate_embed_from_db(s, s.user.display_name, True))

    async def requeue_db(self, message):
        can_manual = str(message.author.id) in self.admin_users
        if not can_manual:
            await message.add_reaction('<:eming:572201816792629267>')
            return
        args = message.content.split(' ')
        if len(args) < 2:
            await message.channel.send("This command will re-process an old score to be fixed after genie changes.\n"
                                       "Usage: `%sredo [score_id]`" % self.command_prefix)
            return

        game = 'ddr'
        if 'iidx' in args[1]:
            game = 'iidx'
            args[1] = args[1].strip('iidx')
            st = IIDXScore
        else:
            st = Score

        if not RepresentsInt(args[1]):
            await message.channel.send("`%s` is not a number!\n"
                                        "Usage: `%sredo [screenshot_id]`" % (args[1], self.command_prefix))
            return

        s = st.get_or_none(id=args[1])
        if s is None:
            await message.channel.send("I can't find a score with ID `%s`" % args[1])
            return

        timestamp = s.file_name.split('-')[1].strip('.jpg')

        await self.db_add_queue.put(DBTaskWorkItem(s.user.id, s.file_name, timestamp, redo=True, game=game))

        await message.channel.send("Added score ID `%s` to the reprocessing queue. (It may take a moment to reprocess)"
                                   % args[1])

    async def manual_db(self, message):
        can_manual = str(message.author.id) in self.admin_users
        if not can_manual:
            await message.add_reaction('<:eming:572201816792629267>')
            return

        args = message.content.split(' ')
        if len(args) < 4:
            await message.channel.send("This command will manually process archived screenshots.\n"
                                       "Usage: `%smanual [discordid] [filename] [timestamp]`" % self.command_prefix)
            return

        if not RepresentsInt(args[1]) or not RepresentsInt(args[3]):
            await message.channel.send("Invalid args.\n"
                                       "Usage: `%smanual [discordid] [filename] [timestamp]`" % self.command_prefix)
            return

        if not os.path.exists("archive/%s/%s" % (args[1], args[2])):
            await message.channel.send("I couldn't find the screenshot at `archive/%s/%s`" % (args[1], args[2]))
            return

        game = 'ddr'
        if 'iidx' in args:
            game = 'iidx'

        await self.db_add_queue.put(DBTaskWorkItem(int(args[1]), args[2], int(args[3]), redo=False, game=game))

        await message.channel.send("Added file `archive/%s/%s` to the processing queue."
                                   % (args[1], args[2]))

    async def help_command(self, message):
        await message.channel.send("Hi! I'm KitsuneBot! I can do various actions related to Bemani games and e-amusement!\n"
                                   "To use commands simply put `%s` before a command name listed below!\n"
                                   "Have a look at the commands here <https://github.com/cyberkitsune/DDRBot/wiki/Commands>\n"
                                   "I'm made by <@109500246106587136> so feel free to ask them any questions" % self.command_prefix)
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
        args = message.content.split(" ", 1)
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
        if not isinstance(message.channel, discord.TextChannel):
            await message.channel.send("Sorry, you can't run this in a DM.")
            return

        can_auth = message.author.id == message.channel.guild.owner_id
        if not can_auth:
            can_auth = str(message.author.id) in self.admin_users

        if not can_auth:
            await message.channel.send("Sorry, only bot admins or guild owners can authorize channels.")
            return

        if 'reporting' not in self.authorized_channels:
            self.authorized_channels['reporting'] = []
        if str(message.channel.id) not in self.authorized_channels['reporting']:
            self.authorized_channels['reporting'].append(str(message.channel.id))
            await message.channel.send("Added this channel to the reporting list!")
        else:
            await message.channel.send("This channel is already a reporting destination! Removing...")
            self.authorized_channels['reporting'].remove(str(message.channel.id))

        save_json('channels.json', self.authorized_channels)

    async def link_command(self, message):
        if not isinstance(message.channel, discord.DMChannel):
            if str(message.author.id) not in self.linked_eamuse:
                await message.channel.send("Your e-amusement account is not linked!")
                await message.channel.send("Use this command in a DM with me to link your e-amusement account! **Do not use this command in public**")
                await message.channel.send("Usage:\n```%slink [username] [password] [otp (optional)]```" % self.command_prefix)
                await message.channel.send("```The bot will not save or log your username or password.\n"
                                           "A token is saved instead and can be revoked by logging in to the e-amusement app if you ever feel the need.\n\n"
                                           "You can review the code for this if you'd like over on github (it's open source)\n "
                                           "https://github.com/cyberkitsune/DDRBot/blob/master/DDRBot.py```")
            else:
                await message.channel.send("Your e-amusement account is linked!")
                await message.channel.send("Use this command in a DM with me to link a different e-amusement account or to login again!")
            return
        args = message.content.split(" ")
        if len(args) < 3:
            await message.channel.send("Usage:\n```%slink [username] [password] [otp (optional)]```" % self.command_prefix)
            await message.channel.send("```The bot will not save or log your username or password.\n"
                                       "A token is saved instead and can be revoked by logging in to the e-amusement app if you ever feel the need.\n\n"
                                       "You can review the code for this if you'd like over on github (it's open source)\n "
                                       "https://github.com/cyberkitsune/DDRBot/blob/master/DDRBot.py```")
            return
        eal = EALink()
        if len(args) > 3:
            eal.login(args[1], args[2], args[3])
        else:
            eal.login(args[1], args[2])

        if eal.logged_in:
            self.linked_eamuse[str(message.author.id)] = [eal.cookies[0], eal.cookies[1]]
            await message.channel.send("Logged in! Your e-amsuement account is linked!\n"
                                       "You can now use features of the bot that require e-amusement")
            await message.channel.send("The bot will automatically DM you new screenshots you save to your e-amusement"
                                       "account. To opt-out of this feature you can type `%sauto off`\nOtherwise, no "
                                       "action is required" % self.command_prefix)
            if str(message.author.id) not in self.auto_users:
                self.add_autos.append(str(message.author.id))

            save_json("linked.json", self.linked_eamuse)
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
                                       "```%sauto (on | off)```" % self.command_prefix)
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

    async def genie_command(self, message):
        if not os.path.exists("DDR_GENIE_ON"):
            await message.channel.send("DDR GENIE (BETA) is not enabled on this bot instance.")
            return

        from DDRGenie.DDRDataTypes import DDRScreenshot, DDRParsedData
        from DDRGenie.IIDXDataTypes import IIDXScreenshot, IIDXParsedData
        from PIL import Image
        import io
        args = message.content.split(' ')
        if len(args) < 2 or 'http' not in args[1]:
            await message.channel.send("Send me a URL to a DDR screenshot and I'll try and parse it.")
            return
        async with message.channel.typing():
            await message.channel.send("Please wait, downloading and trying to parse your screenshot...")

            async with aiohttp.ClientSession() as session:
                async with session.get(args[1]) as r:
                    if r.status == 200:
                        data = await r.read()
                    else:
                        data = None
            img = Image.open(io.BytesIO(data))
            if img.width == 400:
                sst = IIDXScreenshot
                pdt = IIDXParsedData
            elif img.width == 600:
                sst = DDRScreenshot
                pdt = DDRParsedData
            else:
                await message.channel.send("The linked image doesn't appear to be either a IIDX or DDR e-amusement screenshot.\n"
                                           "Please note: This only works with e-amusement screenshots, not photos, or screenshots of screenshots.")
                return
            if self.deep_ai is not None:
                img_arr = io.BytesIO()
                img.save(img_arr, format='PNG')
                new_img = await self.upscale_image(img_arr.getvalue())
                img = Image.open(new_img)
                scale_factor = 2
            else:
                scale_factor = 1
            ss = await self.loop.run_in_executor(None, sst, img, scale_factor)
            pd = await self.loop.run_in_executor(None, pdt, ss)
            if isinstance(pd, DDRParsedData):
                harvest_cover(ss, pd)
                emb = generate_embed(pd, pd.dancer_name.value)
                await message.channel.send(embed=emb)
            elif isinstance(pd, IIDXParsedData):
                emb = generate_embed_iidx(pd, pd.dj_name.value)
                await message.channel.send(embed=emb)
            else:
                raise Exception("Unsupported parsed data type. %s is not supported." % type(pd))

    async def top_scores(self, message):
        args = message.content.split(' ')
        if len(args) > 1:
            other_user = True
            u = User.get_or_none(display_name=' '.join(args[1:]))
        else:
            other_user = False
            u = User.get_or_none(id=int(message.author.id))

        if u is None:
            if other_user:
                name = ' '.join(args[1:])
            else:
                name = message.author.name
            await message.channel.send(
                "%s doesn't have any scores recorded! Use the `scores` command or turn `auto` on to start recording scores. [err 1]" % name)
            return

        query = Score.select().where(Score.user == u).order_by(Score.money_score.desc()).limit(3)
        if not query.exists():
            await message.channel.send("%s doesn't have any scores recorded! Use the `scores` command or turn `auto` on to start recording scores. [err 2]" % u.display_name)
        else:
            with message.channel.typing():
                score_embs = []
                name = ''
                for score in query:
                    name = score.user.display_name
                    score_embs.append(generate_embed_from_db(score, name, True))
                await message.channel.send("Top %i scores for %s:" % (len(score_embs), u.display_name))
                for emb in score_embs:
                    await message.channel.send(embed=emb)

    async def bot_leaderboard(self, message):
        users = User.select()
        users_cum_scores = []
        for u in users:
            user_top_scores = {}
            numscores = 0
            for s in Score.select().where(Score.user == u):
                numscores += 1
                if s.song_title not in user_top_scores:
                    user_top_scores[s.song_title] = s.money_score
                else:
                    if user_top_scores[s.song_title] < s.money_score:
                        user_top_scores[s.song_title] = s.money_score
            total = 0
            for song, score in user_top_scores.items():
                total += score

            users_cum_scores.append((u.display_name, total, numscores))

        sorted_t5 = sorted(users_cum_scores, key=lambda x: x[1], reverse=True)[:5]
        emb = discord.Embed()
        emb.title = "Top %i leaders in the KitsuneBot Leaderboard" % len(sorted_t5)
        emb.description = "Determined by their best plays for each recorded song, added together. (1 Score Per Song, PB only)"
        count = 0
        ranks = ['🏅 First', '🥈 Second', '🥉 Third', 'Fourth', 'Fifth']
        for score in sorted_t5:
            emb.add_field(name=ranks[count], value="%s <:verified:680629672735670352> - **%i** points Total (%i Total submitted scores)" %
                                                   (score[0], score[1], score[2]), inline=False)
            count += 1

        emb.set_footer(text='DDR Genie [β]')
        emb.timestamp = datetime.datetime.utcnow()

        await message.channel.send(embed=emb)

    async def csv_command(self, message):
        u = User.get_or_none(id=int(message.author.id))
        if u is None:
            await message.channel.send("You don't have any scores saved! "
                                       "Try running `scores` or `auto` with some screenshots to record them.")
            return 
        
        score_csv = ["ID | Track Title | Track Artist | Type | Difficulty | Grade | Score | EX Score | Combo | Marvelous | Perfect | "
                     "Great | Good | Miss | OK | Time Played"]

        s: Score
        for s in Score.select().where(Score.user == u):
            score_csv.append("%s|%s|%s|%s|%s %s|%s %s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (s.id, s.song_title, s.song_artist,
                                                                               "Single" if not s.doubles_play
                                                                               else "Double", s.difficulty_name, s.difficulty_number,
                                                                                        s.letter_grade, s.full_combo,
                                                                               s.money_score, s.ex_score, s.max_combo,
                                                                               s.marv_count, s.perf_count, s.great_count,
                                                                               s.good_count, s.miss_count, s.OK_count,
                                                                               s.recorded_time))
        final_csv = '\r\n'.join(score_csv)
        await message.channel.send("I've DMed you your score CSV file! Open it with excel or your other favorite spreadsheet"
                                   "software. The delimiter is `|`.")

        user = self.get_user(message.author.id)
        if user is not None:
            dmc = user.dm_channel
            if dmc is None:
                dmc = await user.create_dm()
            f = discord.File(io.StringIO(final_csv), '%s-scores_%s.csv' % (message.author.name, datetime.datetime.utcnow()))
            await dmc.send("Here's your recorded gene scores as of right now!", file=f)

    async def show_screenshots(self, message):
        if str(message.author.id) not in self.linked_eamuse:
            await message.channel.send("Your e-amusement account isn't linked! Use `%slink` to link your account." % self.command_prefix)
            await message.channel.send("Once linked, this command can post your in-game score screenshots to discord.")
            return
        showAll = 'all' in message.content
        eal = EALink(cookies=(self.linked_eamuse[str(message.author.id)][0], self.linked_eamuse[str(message.author.id)][1]))
        photos = eal.get_screenshot_list()
        if len(photos) == 0:
            await message.channel.send("You don't have any unexpired screenshots saved from the last 48h. Go out and get some scores!\n\n"
                                       "Hint: To save screenshots press `1` on the score screen (in DDR) or `0` (in IIDX)")
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
            archive_screenshot(message.author.id, '%s-%s.jpg' % (photo['game_name'], photo['last_play_date']), data)
            if 'dance' in photo['game_name'].lower():
                await self.db_add_queue.put(DBTaskWorkItem(message.author.id, '%s-%s.jpg' % (photo['game_name'], photo['last_play_date']), photo['last_play_date']))
            if 'beatmania' in photo['game_name'].lower():
                await self.db_add_queue.put(
                    DBTaskWorkItem(message.author.id, '%s-%s.jpg' % (photo['game_name'], photo['last_play_date']),
                                   photo['last_play_date'], game='iidx'))
        if len(screenshot_files) > 10:
            screenshot_files = divide_chunks(screenshot_files, 10)
            await message.channel.send("Your screenshots since last check:")
            for fileset in screenshot_files:
                await message.channel.send(files=fileset)
            save_json("shown.json", self.shown_screenshots)
        else:
            await message.channel.send("Your screenshots since last check:", files=screenshot_files)
            save_json("shown.json", self.shown_screenshots)

    async def monitor_task(self):
        if 'reporting' not in self.authorized_channels:
            self.authorized_channels['reporting'] = []
        if len(self.authorized_channels['reporting']) == 0:
            await asyncio.sleep(60)
            self.loop.create_task(self.monitor_task())
            return
        for arcade in self.monitoring_arcades:
            new_users = []
            api = EAGate(arcade.api_key)
            ddr = DDRApi(api)
            try:
                current_users = await self.loop.run_in_executor(None, ddr.fetch_recent_players)
            except Exception:
                current_users = []

            if len(current_users) == 0:
                if not self.warned_no_users:
                    print("[MONITOR] Warning: No current users returned...")
                    for channel_id in self.authorized_channels['reporting']:
                        channel = self.get_channel(channel_id)
                        if channel is not None:
                            await channel.send("Hey! There are no recent users... this could be a bug!!! (Or maintenance)")
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
                print("[MONITOR] %s" % n_message)
                if len(self.authorized_channels['reporting']) > 0:
                    for channel_id in self.authorized_channels['reporting']:
                        channel = self.get_channel(channel_id)
                        if channel is not None:
                            await channel.send(n_message)
        await asyncio.sleep(60)
        self.loop.create_task(self.monitor_task())

    async def feed_task(self):
        if 'feed' not in self.authorized_channels:
            self.authorized_channels['feed'] = []
        if len(self.authorized_channels['feed']) == 0:
            await asyncio.sleep(60)
            self.loop.create_task(self.feed_task())
            return
        new_score = await self.new_scores.get()
        if new_score[1] == 'ddr':
            st = Score
        elif new_score[1] == 'iidx':
            st = IIDXScore
        else:
            await asyncio.sleep(1)
            self.loop.create_task(self.feed_task())
            return
        s = st.get_or_none(id=new_score[0])
        if s is not None:
            emb = generate_embed_from_db(s, s.user.display_name, True)
            for channel_id in self.authorized_channels['feed']:
                channel = self.get_channel(int(channel_id))
                if channel is not None:
                    do_send = False
                    if channel.id == 680575323271856273:
                        do_send = True
                    else:
                        chn_ids = []
                        for member in channel.members:
                            chn_ids.append(member.id)
                        if s.user.id in chn_ids:
                            do_send = True
                    if do_send:
                        await channel.send(embed=emb)

        await asyncio.sleep(1)
        self.loop.create_task(self.feed_task())

    async def auto_task(self):
        if len(self.add_autos) > 0:
            for user_id in self.add_autos:
                self.auto_users[user_id] = 0
            self.add_autos = []
            save_json("auto.json", self.auto_users)

        if len(self.remove_autos) > 0:
            for user_id in self.remove_autos:
                if user_id in self.auto_users:
                    del self.auto_users[user_id]
            self.remove_autos = []
            save_json("auto.json", self.auto_users)

        for user_id in self.auto_users:
            last_time = int(self.auto_users[user_id])
            # Fetch screenshots
            eal = None
            photos = []
            try:
                eal = EALink(cookies=(self.linked_eamuse[str(user_id)][0], self.linked_eamuse[str(user_id)][1]))
                photos = await self.loop.run_in_executor(None, eal.get_screenshot_list)
            except EALoginException as ex:
                if user_id not in self.warned_auto_error:
                    user = self.get_user(user_id)
                    if user is not None:
                        dmc = user.dm_channel
                        if dmc is None:
                            dmc = await user.create_dm()
                        await dmc.send("Hey! You have `%sauto` on but I can't seem to log into your account anymore!\n"
                                       "Please run %slink again to reconnect your account, or do `%sauto off` to disable this feature." %
                                       (self.command_prefix, self.command_prefix, self.command_prefix))
                        print("[AUTO] Warned %s about their login failure." % user.name)
                        self.warned_auto_error.append(user_id)
                    else:
                        print("[AUTO] I couldn't find user %s... Account deleted?" % user_id)
                        self.warned_auto_error.append(user_id)
            except Exception as ex:
                if user_id not in self.warned_auto_error:
                    print("[AUTO] Exception fetching photos for %s\n%s" % (user_id, ex))
                    self.warned_auto_error.append(user_id)
            else:
                if user_id in self.warned_auto_error:
                    self.warned_auto_error.remove(user_id)

            if len(photos) > 0:
                photos = sorted(photos, key=lambda x: int(x['last_play_date']))  # Smallest first
                new_photos = []
                for photo in photos:
                    if int(photo['last_play_date']) > last_time:
                        new_photos.append(photo)
                        last_time = int(photo['last_play_date'])

                if len(new_photos) > 0:
                    print("[AUTO] Sending %i photos to %s" % (len(new_photos), user_id))
                    self.auto_users[user_id] = last_time
                    user = self.get_user(int(user_id))
                    if user is None:
                        print("[AUTO] Warning: can't find user %s" % user_id)
                        continue
                    channel = user.dm_channel
                    if channel is None:
                        await user.create_dm()
                        channel = user.dm_channel

                    screenshot_files = []
                    for photo in new_photos:
                        try:
                            data = eal.get_jpeg_data_for(photo['file_path'])
                        except EALinkException as ex:
                            await channel.send("Hey! I got some weird error trying to automatically pick up this screenshot `%s-%s.jpg`... Let CyberKitsune know!\nDetails:\n"
                                               "```%s```" % (photo['game_name'], photo['last_play_date'], ex.jscontext))
                            print("[AUTO] Hey! I got some weird error trying to automatically pick up this screenshot %s-%s.jpg... Let CyberKitsune know!\nDetails:\n"
                                               "```%s```" % (photo['game_name'], photo['last_play_date'], ex.jscontext))
                            continue
                        screenshot_files.append(discord.File(io.BytesIO(data), '%s-%s.jpg' % ((photo['game_name'], photo['last_play_date']))))
                        archive_screenshot(user.id,
                                           '%s-%s.jpg' % (photo['game_name'], photo['last_play_date']), data)
                        if 'dance' in photo['game_name'].lower():
                            await self.db_add_queue.put(
                                DBTaskWorkItem(user.id, '%s-%s.jpg' % (photo['game_name'], photo['last_play_date']), photo['last_play_date']))
                        if 'beatmania' in photo['game_name'].lower():
                            await self.db_add_queue.put(
                                DBTaskWorkItem(user.id, '%s-%s.jpg' % (photo['game_name'], photo['last_play_date']),
                                               photo['last_play_date'], game='iidx'))
                    if len(screenshot_files) == 0:
                        pass
                    elif len(screenshot_files) > 10:
                        screenshot_files = divide_chunks(screenshot_files, 10)
                        for fileset in screenshot_files:
                            await channel.send(files=fileset)
                    else:
                        await channel.send(files=screenshot_files)
                    save_json("auto.json", self.auto_users)

        await asyncio.sleep(60)
        self.loop.create_task(self.auto_task())

    async def db_task(self):
        db.create_tables([User, Score, IIDXScore])
        while not self.db_add_queue.empty():
            item = await self.db_add_queue.get()
            if not isinstance(item, DBTaskWorkItem):
                print("[DBTask] Warning: Non work-item in queue...")
                continue
            # Check user

            u = User.get_or_none(User.id == int(item.discord_id))
            if u is None:
                u = User.create(id=int(item.discord_id), display_name=self.get_user(item.discord_id).name)

            id_override = None
            if item.game == 'ddr':
                st = Score
            elif item.game == 'iidx':
                st = IIDXScore
            else:
                continue
            test_score: st = st.get_or_none(st.user == u, st.file_name == item.image_filename)
            if test_score is not None:
                if not item.redo:
                    print("[DBTask] Skipping duplicate score for %s (%s)..." % (u.display_name, item.image_filename))
                    continue
                else:
                    print("[DBTask] Redoing duplicate score for %s (%s)" % (u.display_name, item.image_filename))
                    id_override = test_score.id
                    test_score.delete_instance()

            from DDRGenie.DDRDataTypes import DDRScreenshot, DDRParsedData
            from DDRGenie.IIDXDataTypes import IIDXScreenshot, IIDXParsedData
            from PIL import Image
            import io
            if item.game == 'ddr':
                sst = DDRScreenshot
                pdt = DDRParsedData
            elif item.game == 'iidx':
                sst = IIDXScreenshot
                pdt = IIDXParsedData
            else:
                print("[DBTask] Unhandled game type %s, skipping..." % item.game)
                continue
            img = Image.open("./archive/%s/%s" % (item.discord_id, item.image_filename))
            if self.deep_ai is not None:
                img_arr = io.BytesIO()
                img.save(img_arr, format='PNG')
                try:
                    new_img = await self.upscale_image(img_arr.getvalue())
                    img = Image.open(new_img)
                    scale_factor = 2
                except Exception as ex:
                    print("[DBTask] Can't upscale image. Defaulting to 1x. Err: %s" % ex)
                    scale_factor = 1
            else:
                scale_factor = 1
            try:
                ss = await self.loop.run_in_executor(None, sst, img, scale_factor)
                sd = await self.loop.run_in_executor(None, pdt, ss)
            except Exception as ex:
                print("[DBTask] Can't parse image, skipping... Ex: %s" % ex)
                continue
            if isinstance(sd, DDRParsedData):
                harvest_cover(ss, sd)
                print("[DBTask] Inserting score for %s; SONG %s GRADE %s SCORE %s EX %s TSTAMP %s" %
                      (u.display_name, sd.song_title, sd.play_letter_grade, sd.play_money_score,
                       sd.play_ex_score, sd.date_stamp))
                try:
                    if '*' in sd.play_ex_score.value:
                        exscore_int = int(sd.play_ex_score.value.split('*')[0])
                    else:
                        exscore_int = int(sd.play_ex_score.value)

                    sc_time = datetime.datetime.utcfromtimestamp(int(item.timestamp_string))
                    if id_override is not None:
                        s = Score.create(id=id_override, user=u, song_title=sd.song_title.value, song_artist=sd.song_artist.value,
                                         letter_grade=sd.play_letter_grade,
                                         full_combo=sd.play_full_combo, doubles_play=('DOUBLE' in sd.chart_play_mode.value),
                                         money_score=int(sd.play_money_score.value),
                                         ex_score=exscore_int, marv_count=int(sd.score_marv_count.value),
                                         perf_count=int(sd.score_perfect_count.value),
                                         great_count=int(sd.score_great_count.value), good_count=int(sd.score_good_count.value),
                                         OK_count=int(sd.score_OK_count.value),
                                         miss_count=int(sd.score_miss_count.value), max_combo=int(sd.play_max_combo.value),
                                         file_name=item.image_filename,
                                         difficulty_number=int(sd.chart_difficulty_number.value),
                                         difficulty_name=sd.chart_difficulty.value, name_confidence=sd.title_conf,
                                         recorded_time=sc_time)
                    else:
                        s = Score.create(user=u, song_title=sd.song_title.value, song_artist=sd.song_artist.value, letter_grade=sd.play_letter_grade,
                                 full_combo=sd.play_full_combo, doubles_play=('DOUBLE' in sd.chart_play_mode.value), money_score=int(sd.play_money_score.value),
                                 ex_score=exscore_int, marv_count=int(sd.score_marv_count.value), perf_count=int(sd.score_perfect_count.value),
                                 great_count=int(sd.score_great_count.value), good_count=int(sd.score_good_count.value), OK_count=int(sd.score_OK_count.value),
                                 miss_count=int(sd.score_miss_count.value), max_combo=int(sd.play_max_combo.value), file_name=item.image_filename,
                                     difficulty_number=int(sd.chart_difficulty_number.value), difficulty_name=sd.chart_difficulty.value, name_confidence=sd.title_conf,
                                     recorded_time=sc_time)
                except ValueError as ex:
                    print("[DBTASK] ValueError doing last insert. E: %s" % ex)
                    continue

            elif isinstance(sd, IIDXParsedData):
                sc_time = datetime.datetime.utcfromtimestamp(int(item.timestamp_string))
                print("[DBTask] Inserting IIDX for %s; SONG %s GRADE %s EX %s TSTAMP %s" %
                      (u.display_name, sd.song_title, sd.play_dj_level, sd.play_ex_score, sd.date_time))
                try:
                    if id_override is not None:
                        s = IIDXScore.create(id=id_override, user=u, song_title=sd.song_title.value,
                                             song_artist=sd.song_artist.value, difficulty=sd.chart_difficulty.value,
                                             clear_type=sd.play_clear_type.value, dj_grade=sd.play_dj_level.value,
                                             double_play=('DP' in sd.chart_play_mode.value), ex_score=int(sd.play_ex_score.value),
                                             p_great_count=int(sd.score_rainbow_count.value), great_count=int(sd.score_great_count.value),
                                             good_count=int(sd.score_good_count.value), bad_count=int(sd.score_bad_count.value),
                                             poor_count=int(sd.score_poor_count.value), combo_break=int(sd.score_combo_break.value),
                                             miss_count=int(sd.play_miss_count.value), fast_count=int(sd.score_fast_count.value),
                                             slow_count=int(sd.score_slow_count.value), overall_confidence=sd.overall_conf,
                                             recorded_time=sc_time, file_name=item.image_filename)
                    else:
                        s = IIDXScore.create(user=u, song_title=sd.song_title.value,
                                             song_artist=sd.song_artist.value, difficulty=sd.chart_difficulty.value,
                                             clear_type=sd.play_clear_type.value, dj_grade=sd.play_dj_level.value,
                                             double_play=('DP' in sd.chart_play_mode.value),
                                             ex_score=int(sd.play_ex_score.value),
                                             p_great_count=int(sd.score_rainbow_count.value),
                                             great_count=int(sd.score_great_count.value),
                                             good_count=int(sd.score_good_count.value),
                                             bad_count=int(sd.score_bad_count.value),
                                             poor_count=int(sd.score_poor_count.value),
                                             combo_break=int(sd.score_combo_break.value),
                                             miss_count=int(sd.play_miss_count.value),
                                             fast_count=int(sd.score_fast_count.value),
                                             slow_count=int(sd.score_slow_count.value), overall_confidence=sd.overall_conf,
                                             recorded_time=sc_time, file_name=item.image_filename)
                except ValueError as ex:
                    print("[DBTASK] ValueError doing last insert. E: %s" % ex)
                    continue
            else:
                continue

            s.save()
            if not item.redo:
                await self.new_scores.put((s.id, item.game))

            await asyncio.sleep(2)  # Free up time for catch up

        db.commit()
        await asyncio.sleep(10)
        self.loop.create_task(self.db_task())

    async def upscale_image(self, image):
        async with aiohttp.ClientSession() as session:
            data = {'image': image}
            headers = {'api-key': '%s' % self.deep_ai.strip()}
            async with session.post("https://api.deepai.org/api/waifu2x", data=data, headers=headers) as r:
                js = await r.json()
                if 'output_url' in js:
                    r1 = await session.get(js['output_url'])
                    c = await r1.read()
                    reqdata = io.BytesIO(c)
                    return reqdata
                else:
                    raise Exception("DeepAI didn't return an upscaled image...\nOutput: %s", js)


if __name__ == "__main__":
    bot = DDRBotClient(sys.argv[2])
    try:
        bot.run(sys.argv[1])
    except YeetException:
        exit(0)
    except Exception as ex:
        raise ex
