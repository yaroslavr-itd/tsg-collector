from sys import argv

from ContractDispatcher import ContractDispatcher
from CollectorBot import CollectorBot


def main():
    key = argv[1]
    contract_address = argv[2]
    bot_access_key = argv[3]
    node = 'https://ropsten.infura.io/9S2cUwgCk4jYKYG85rxJ'
    contract_dispatcher = ContractDispatcher(key, contract_address, node)
    bot = CollectorBot(bot_access_key)
    bot.set_contract_dispatcher(contract_dispatcher)

    del key
    del contract_address
    del bot_access_key

    del argv[1:4]
    bot.start_bot(idle=True)


if __name__ == '__main__':
    main()

