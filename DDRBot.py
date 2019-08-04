import discord, sys
from py573jp.EAGate import EAGate
from py573jp.DDRPage import DDRApi
from Misc import RepresentsInt

class DDRBotClient(discord.Client):
    admin_users = []
    command_handlers = {}
    command_prefix = 'k!'
    generic_eamuse_session = None

    def __init__(self, session_id):
        self.generic_eamuse_session = session_id
        self.command_handlers['help'] = self.help_command
        self.command_handlers['lookup'] = self.lookup_command
        super().__init__()

    async def on_ready(self):
        print("DDRBot is ready!")

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
                except Exception as ex:
                    await message.channel.send("Oops! uwu an error occured running that command.\nTechnical Details of Error: ```\n %s```" % ex)
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




if __name__ == "__main__":
    bot = DDRBotClient(sys.argv[2])
    bot.run(sys.argv[1])
