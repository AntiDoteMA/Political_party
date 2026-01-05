import logging
import gspread
import gettext
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

from config import TELEGRAM_TOKEN, SHEET_NAME

# --- I18N SETUP ---
def set_language(lang_code):
    """Sets the application language."""
    translation = gettext.translation('messages', localedir='locales', languages=[lang_code])
    translation.install()
    return translation.gettext

# A global dictionary to hold the translator function for each user
user_translators = {}

def get_translator(user_id):
    """Returns the translator function for a given user, defaults to English."""
    return user_translators.get(user_id, set_language('en'))

# --- CONFIGURATION ---
TOKEN = TELEGRAM_TOKEN
CREDENTIALS_FILE = 'credentials.json'
ADMIN_USER_IDS = [123456789]  # Replace with the actual Telegram User IDs of admins

# --- DATA STORAGE (IN-MEMORY) ---
known_user_ids = set()

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- GOOGLE SHEETS SETUP ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def save_to_google_sheets(user_data):
    """Authenticates and appends data to the Google Sheet."""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        
        if not sheet.acell('A1').value:
            sheet.append_row(['User ID', 'First Name', 'Username', 'Interest', 'Barrier', 'Timing', 'Contribution', 'Feedback'])
            
        row = [
            str(user_data.get('id')),
            user_data.get('first_name'),
            f"@{user_data.get('username')}" if user_data.get('username') else "No Username",
            user_data.get('interest'),
            user_data.get('barrier'),
            user_data.get('timing'),
            user_data.get('contribution'),
            user_data.get('feedback')
        ]
        
        sheet.append_row(row)
        logging.info(f"Data saved for user {user_data.get('first_name')}.")
        
    except Exception as e:
        logging.error(f"Failed to save to Google Sheet: {e}")

# --- CONVERSATION STATES ---
CHOOSE_LANG, INTEREST, BARRIERS, TIMING, CONTRIBUTION, FEEDBACK = range(6)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation and asks for language preference."""
    reply_keyboard = [['English', 'العربية']]
    await update.message.reply_text(
        "Please choose your language: / الرجاء اختيار لغتك:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSE_LANG

async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the user's language and starts the survey."""
    user = update.effective_user
    lang_choice = update.message.text
    
    if 'English' in lang_choice:
        lang_code = 'en'
    elif 'العربية' in lang_choice:
        lang_code = 'ar'
    else:
        # Default to English if the choice is unclear
        lang_code = 'en'

    # Store the translator function for this user
    user_translators[user.id] = set_language(lang_code)
    _ = get_translator(user.id)
    
    known_user_ids.add(user.id)
    context.user_data['id'] = user.id
    context.user_data['username'] = user.username
    context.user_data['first_name'] = user.first_name
    
    reply_keyboard = [[_('Fully Committed'), _('Interested but Busy')], [_('Just Observing'), _('Not Interested')]]

    # Use the original msgid for translation (no LTR mark) then insert
    # a Left-to-Right mark before the numbered item for RTL languages.
    message = _("Hi {first_name}! We are upgrading our political group structure.\n\n1. "
                "How would you describe your current interest in building this party?")
    message = message.format(first_name=user.first_name)
    # remember user's language for later handlers
    context.user_data['lang'] = lang_code

    if lang_code == 'ar':
        message = message.replace('\n\n1.', '\n\n\u200E1.')
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return INTEREST
    
async def interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ = get_translator(update.effective_user.id)
    context.user_data['interest'] = update.message.text
    reply_keyboard = [[_('Bad Timing'), _('Meetings too long')], [_('No clear agenda'), _('I forget')], [_('Prefer text updates')]]
    await update.message.reply_text(
        _("2. Thanks! We noticed attendance is low. What is the main reason you usually can't make the meetings?"),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return BARRIERS

async def barriers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ = get_translator(update.effective_user.id)
    context.user_data['barrier'] = update.message.text
    reply_keyboard = [[_('Weekday Evenings'), _('Weekends')], [_('Lunch Breaks'), _('Async (Text only)')]]
    await update.message.reply_text(
        _("3. If we reorganized, what time block works best for you?"),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TIMING

async def timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ = get_translator(update.effective_user.id)
    context.user_data['timing'] = update.message.text
    reply_keyboard = [[_('Social Media/PR'), _('Writing Policy')], [_('Recruitment'), _('Just Voting')], [_('No tasks right now')]]
    await update.message.reply_text(
        _("4. Meetings aside, how would you prefer to contribute right now?"),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONTRIBUTION

async def contribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ = get_translator(update.effective_user.id)
    context.user_data['contribution'] = update.message.text
    await update.message.reply_text(
        _("5. Last question (Reply with text):\n"
          "In one sentence, what is one thing we could do to make this group more exciting for you?"),
        reply_markup=ReplyKeyboardRemove()
    )
    return FEEDBACK

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ = get_translator(update.effective_user.id)
    context.user_data['feedback'] = update.message.text
    await update.message.reply_text(_("Saving your answers... please wait a moment."))
    save_to_google_sheets(context.user_data)
    await update.message.reply_text(
        _("✅ Done! Your feedback has been recorded. We will use this to improve our meetings.")
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ = get_translator(update.effective_user.id)
    await update.message.reply_text(_("Survey cancelled."), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ = get_translator(update.effective_user.id)
    user_id = update.effective_user.id
    help_text = (
        _("Here are the available commands:\n"
          "/start - Begin the survey to provide your feedback.\n"
          "/cancel - Stop the survey at any time.\n"
          "/help - Show this help message.")
    )
    
    if user_id in ADMIN_USER_IDS:
        help_text += _("\n\n--- Admin Commands ---\n/broadcast [message] - Send a message to all users.")
        
    await update.message.reply_text(help_text)

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _ = get_translator(update.effective_user.id)
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text(_("You are not authorized to use this command."))
        return
        
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text(_("Please provide a message to send. Usage: /broadcast [your message]"))
        return
        
    sent_count = 0
    failed_count = 0
    await update.message.reply_text(_("Starting broadcast to {count} users...").format(count=len(known_user_ids)))
    
    for uid in known_user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent_count += 1
        except Exception as e:
            logging.error(f"Failed to send message to user {uid}: {e}")
            failed_count += 1
            
    await update.message.reply_text(_("Broadcast finished.\nSent: {sent_count}\nFailed: {failed_count}").format(sent_count=sent_count, failed_count=failed_count))

def create_conversation_handler():
    """Creates and returns the ConversationHandler for the survey."""
    return ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_lang)],
            INTEREST: [MessageHandler(filters.TEXT & ~filters.COMMAND, interest)],
            BARRIERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, barriers)],
            TIMING: [MessageHandler(filters.TEXT & ~filters.COMMAND, timing)],
            CONTRIBUTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, contribution)],
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

# --- MAIN ---
if __name__ == '__main__':
    # Set default language to English
    _ = set_language('en')
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = create_conversation_handler()

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('broadcast', broadcast_command))
    
    print(_("Bot is polling..."))
    application.run_polling()
