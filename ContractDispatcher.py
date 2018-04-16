from web3 import Web3, HTTPProvider, Account, __version__
from ethtoken.abi import EIP20_ABI


class ContractDispatcher:
    def __init__(self, key: str, contract_address: str, node_address: str):
        self._account = Account.privateKeyToAccount(key)
        self._contract_address = contract_address
        self._node_address = node_address

        self.w3 = Web3(HTTPProvider(self._node_address))
        self.contract = self.w3.eth.contract(address=self._contract_address, abi=EIP20_ABI)

        self._balanceOf = self.contract.functions.balanceOf
        self._totalSupply = self.contract.functions.totalSupply
        self._transfer = self.contract.functions.transfer

    def balance_of(self, owner: str) -> int:
        transaction = {
            'from': self._account.address,
            'to': self._contract_address
        }
        result = self._balanceOf(owner).call(transaction)
        del transaction
        return result

    def total_supply(self) -> int:
        transaction = {
            'from': self._account.address,
            'to': self._contract_address
        }
        result = self._totalSupply().call(transaction)
        del transaction
        return result

    def transfer(self, to: str, value: int) -> str:
        nonce = self.w3.eth.getTransactionCount(self._account.address)
        transaction = self._transfer(to, value).buildTransaction({
            'chainIf': 3,
            'gas': 90000,
            'gasPrice': Web3.toWei(5, 'gwei'),
            'nonce': nonce
        })
        signed_transaction = self._account.signTransaction(transaction)

        self.w3.eth.sendRawTransaction(signed_transaction.rawTransaction)
        del transaction
        del nonce
        return self.w3.toHex(signed_transaction.hash)
