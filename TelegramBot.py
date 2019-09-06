from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram import ChatAction
import sys, logging, json, os, io
from py573jp.EALink import EALink, EALinkException

updater = Updater(token=sys.argv[1], use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

linked_accounts = {}

def save_accounts():
    global linked_accounts
    js = json.dumps(linked_accounts)
    with open("tg_linked.json", 'w') as f:
        f.write(js)

def load_accounts():
    global linked_accounts
    if os.path.exists("tg_linked.json"):
        with open("tg_linked.json", 'r') as f:
            txt = f.read()
        linked_accounts = json.loads(txt)

def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, parse_mode='Markdown', text="Hello! I'm bemani screenshot bot! I can help you with your e-amusement screenshots\n\n"
                                                                  "*Commands*\n/start - This text!\n"
                                                                  "/link - Link your e-amusement account\n"
                                                                  "/screenshots - See your unexpired Bemani Screenshots\n"
                                                                                         "\nBot made by @CyberKitsune")

def link(update, context):
    global linked_accounts
    print("%s is linking their account!" % update.message.from_user.username)
    args = update.message.text.split(" ")
    if len(args) < 3:
        context.bot.send_message(chat_id=update.message.chat_id, parse_mode='Markdown', text="Use this command to link your e-amusement account!\n"
                                                                                             "Usage:\n"
                                                                                             "```link [username] [password] [OTP (optional)]```")
        print("%s didn't link..." % update.message.from_user.username)
        return
    username = args[1]
    password = args[2]
    otp = None
    if len(args) == 4:
        otp = args[3]
    eal = EALink()
    try:
        eal.login(username, password, otp)
    except EALinkException as ex:
        context.bot.send_message(chat_id=update.message.chat_id, parse_mode='Markdown', text="An error occured linking your account! Details:\n```%s```" % ex)
    if eal.logged_in:
        linked_accounts[update.message.from_user.username] = (eal.cookies[0], eal.cookies[1])
        context.bot.send_message(chat_id=update.message.chat_id, text="Successfully logged in!")
        print("%s successfully linked!" % update.message.from_user.username)
        save_accounts()
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Couldn't log in!")
        print("%s had login issues!" % update.message.from_user.username)


def screenshots(update, context):
    global linked_accounts
    print("%s requested screenshots!" % update.message.from_user.username)
    if update.message.from_user.username not in linked_accounts:
        context.bot.send_message(chat_id=update.message.chat_id, text="You're not logged in! Use /link to link your e-amusement account!")
        print("%s wasn't logged in!" % update.message.from_user.username)
        return

    eal = EALink(cookies=(linked_accounts[update.message.from_user.username][0],linked_accounts[update.message.from_user.username][1]))
    shots = None
    try:
        shots = eal.get_screenshot_list()
    except EALinkException as ex:
        context.bot.send_message(chat_id=update.message.chat_id, parse_mode='Markdown',
                                 text="An error occured getting screenshots! Details:\n```%s```" % ex)
        return
    if len(shots) == 0:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="You have no unexpired screenshots right now! Go out and get some scores!")
        print("%s has no screenshots!" % update.message.from_user.username)
        return

    context.bot.send_message(chat_id=update.message.chat_id, text="Fetching your %i screenshots..." % len(shots))
    print("%s is downloading %i screenshots" % (update.message.from_user.username, len(shots)))
    context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
    photo_datas = []
    for photo in shots:
        data = eal.get_jpeg_data_for(photo['file_path'])
        photo_datas.append(data)
    for data in photo_datas:
        context.bot.send_photo(chat_id=update.message.chat_id, photo=io.BytesIO(data))

start_handler = CommandHandler('start', start)
link_handler = CommandHandler('link', link)
screenshot_handler = CommandHandler('screenshots', screenshots)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(link_handler)
dispatcher.add_handler(screenshot_handler)


if __name__ == "__main__":
    load_accounts()
    print("Launching bot...")
    updater.start_polling()