from telegram import ReplyKeyboardMarkup, Update, User
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def tx_to_url(transaction: str):
    return 'https://ropsten.etherscan.io/tx/{}'.format(transaction)


def list_to_keyboard(keys_list, keys_in_row):
    keyboard = []
    start_index = 0
    for keys in keys_in_row:
        keyboard.append(keys_list[start_index:start_index + keys])
        start_index += keys
    return keyboard


class CollectorBot:
    MAIN_MENU_STATE, SET_PRIVATE_INFO_STATE, SET_COMPANY_INFO_STATE, TYPING_REPLY_STATE, TYPING_CHOICE_STATE = range(5)
    MAIN_MENU = ('👤Set private info', '🏢Set company info', '📋Show all', '🎁Get reward')
    PRIVATE_INFO_MENU = ('✍🏻 Name', '💳Wallet')
    COMPANY_INFO_MENU = ('✍🏻 Company name', '👨👥Total customers', '📆LTV months', '💵LTV dollars', '📈ARPU')

    MAIN_MARKUP = ReplyKeyboardMarkup(
        list_to_keyboard(MAIN_MENU, (2, 2)),
        resize_keyboard=True
    )
    PRIVATE_MARKUP = ReplyKeyboardMarkup(
        list_to_keyboard(PRIVATE_INFO_MENU, (2,)),
        resize_keyboard=True,
        one_time_keyboard=True
    )
    COMPANY_MARKUP = ReplyKeyboardMarkup(
        list_to_keyboard(COMPANY_INFO_MENU, (2, 3)),
        resize_keyboard=True,
        one_time_keyboard=True
    )

    # CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

    def __init__(self, access_token: str):
        self.updater = Updater(access_token)
        self._contract_dispatcher = None
        self.users_id = []

        self._init()

    def _init(self):
        entry_points = [CommandHandler('start', self._start)]
        states = {
            self.MAIN_MENU_STATE: [
                RegexHandler('^{}$'.format(self.MAIN_MENU[0]), self._private_info),
                RegexHandler('^{}$'.format(self.MAIN_MENU[1]), self._company_info),
                RegexHandler('^{}$'.format(self.MAIN_MENU[2]), self._show_all, pass_user_data=True),
                RegexHandler('^{}$'.format(self.MAIN_MENU[3]), self._get_reward, pass_user_data=True),
            ],
            self.SET_PRIVATE_INFO_STATE: [
                RegexHandler('^({})$'.format('|'.join(self.PRIVATE_INFO_MENU)),
                             self._private_choice,
                             pass_user_data=True)
            ],
            self.SET_COMPANY_INFO_STATE: [
                RegexHandler('^({})$'.format('|'.join(self.COMPANY_INFO_MENU)),
                             self._company_choice,
                             pass_user_data=True)
            ],
            self.TYPING_REPLY_STATE: [
                MessageHandler(Filters.text,
                               self._received_information,
                               pass_user_data=True),
            ]
        }
        # fallbacks = [RegexHandler('^Get reward$', self._get_reward, pass_user_data=True)]
        conv_handler = ConversationHandler(
            entry_points=entry_points,
            states=states,
            fallbacks=[RegexHandler('qwerty', lambda bot, update: print())],
            allow_reentry=True
        )
        self.updater.dispatcher.add_handler(conv_handler)
        self.updater.dispatcher.add_error_handler(error)

    def _start(self, bot, update: Update):
        current_user: User = update.effective_user
        if current_user.id in self.users_id:
            update.message.reply_text('Welcome back, {}❗️'.format(current_user.first_name),
                                      reply_markup=self.MAIN_MARKUP)
            return self.MAIN_MENU_STATE
        else:
            update.message.reply_text('Hello, {}❗️Set up your account firstly, please'.format(current_user.first_name),
                                      reply_markup=self.PRIVATE_MARKUP)
            return self.SET_PRIVATE_INFO_STATE

    def _private_info(self, bot, update: Update):
        update.message.reply_text('🆗, set up your account 👤',
                                  reply_markup=self.PRIVATE_MARKUP)
        return self.SET_PRIVATE_INFO_STATE

    def _company_info(self,  bot, update: Update):
        update.message.reply_text('Good, now tell me some about your company 🏢',
                                  reply_markup=self.COMPANY_MARKUP)
        return self.SET_COMPANY_INFO_STATE

    def _private_choice(self, bot, update: Update, user_data):
        if 'private' not in user_data:
            user_data['private'] = {}
        text = update.message.text
        user_data['choice'] = text.lower()
        user_data['category'] = 'private'
        update.message.reply_text('🆗, set your {}'.format(text.lower()))

        return self.TYPING_REPLY_STATE

    def _company_choice(self, bot, update: Update, user_data):
        if 'company' not in user_data:
            user_data['company'] = {}
        text = update.message.text
        user_data['choice'] = text.lower()
        user_data['category'] = 'company'
        update.message.reply_text('🆗, set {}'.format(text.lower()))

        return self.TYPING_REPLY_STATE

    def _received_information(self, bot, update: Update, user_data):
        text = update.message.text

        category = user_data['category']
        if category == 'private':
            user_data['private'][user_data['choice']] = text
            del user_data['choice']
            all_set = all(private_category.lower() in user_data[category] for private_category in self.PRIVATE_INFO_MENU)
            if all_set:
                if update.effective_user.id not in self.users_id:
                    self.users_id.append(update.effective_user.id)
                update.message.reply_text("Great❗️Your account successfully set up",
                                          reply_markup=self.MAIN_MARKUP)
                return self.MAIN_MENU_STATE
            else:
                update.message.reply_text("Good. Set remaining fields 📝",
                                          reply_markup=self.PRIVATE_MARKUP)
                return self.SET_PRIVATE_INFO_STATE
        elif category == 'company':
            user_data['company'][user_data['choice']] = text
            del user_data['choice']
            all_set = all(
                private_category.lower() in user_data[category] for private_category in self.COMPANY_INFO_MENU)
            if all_set:
                update.message.reply_text("Great❗️Now we know all about you company 😉",
                                          reply_markup=self.MAIN_MARKUP)
                return self.MAIN_MENU_STATE
            else:
                update.message.reply_text("Good. Set remaining fields 📝",
                                          reply_markup=self.COMPANY_MARKUP)
                return self.SET_COMPANY_INFO_STATE

    def _show_all(self, bot, update: Update, user_data):
        info = 'You\'ve provided next information 📝\n'
        if 'private' in user_data:
            info += '<b>👤Private info:</b>\n'
            info += '\n'.join('{} - {}'.format(key, value) for key, value in user_data['private'].items())
        if 'company' in user_data:
            info += '\n\n<b>🏢Company info:</b>\n'
            info += '\n'.join('{} - {}'.format(key, value) for key, value in user_data['company'].items())

        update.message.reply_text(info, markup=self.MAIN_MARKUP, parse_mode='html')

        return self.MAIN_MENU_STATE

    def _get_reward(self, bot, update: Update, user_data):
        if self._contract_dispatcher is None:
            update.message.reply_text('Sorry, but i can\'t send tokens right now 🙁',
                                      reply_markup=self.MAIN_MARKUP)
        else:
            transaction = self._contract_dispatcher.transfer(user_data['private']['💳wallet'], 5)
            url = tx_to_url(transaction)
            update.message.reply_text('🎉 I\'ve sent you 5 tokens. Check it on 👇 \n{}'.format(url),
                                      reply_markup=self.MAIN_MARKUP)

        return self.MAIN_MENU_STATE

    def start_bot(self, timeout=120, idle=False):
        self.updater.start_polling(timeout=timeout)
        if idle:
            self.updater.idle()

    def set_contract_dispatcher(self, contract_dispatcher):
        self._contract_dispatcher = contract_dispatcher

