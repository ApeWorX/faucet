import json
import os
from pathlib import Path
from typing import Annotated, list

import uvicorn
from ape import chain, networks
from ape.api.accounts import ImpersonatedAccount
from ape.exceptions import ApeException
from ape.types import AddressType
from ape_accounts import KeyfileAccount
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import AnyUrl, BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from tokenlists import TokenListManager

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if account_json := os.environ.get("BOT_ACCOUNT_JSON"):
    path = Path(__file__).parent / "bot.json"
    path.write_text(account_json)

ACCOUNT = KeyfileAccount(keyfile_path=(Path(__file__).parent / "bot.json"))
ACCOUNT.set_autosign(True, passphrase="anvil")  # NOTE: Bundle account keyfile when building

FAUCET_LIMIT = int(os.environ.get("FAUCET_TRANSFER_LIMIT", 10**18))

NETWORK_TRIPLE = os.environ.get("APE_FOUNDRY_HOST", "http://localhost:8545")


class FaucetResponse(BaseModel):
    txn_hash: str
    txn_url: AnyUrl | None = None
    balance: int


@app.get("/transfer/{address}")
@limiter.limit("1/day")
async def transfer(
    request: Request,
    address: str,
    amount: Annotated[int, Query(gt=0, lt=FAUCET_LIMIT)] = FAUCET_LIMIT,
    gas_limit: Annotated[int, Query(gt=21_000, lt=50_000)] = 35_000,
) -> FaucetResponse:
    """
    Send `amount` ether to `address`, with `gas_limit` given to transaction.

    Defaults to 1 ether and 35k gas.
    """
    with networks.parse_network_choice(NETWORK_TRIPLE) as provider:
        # NOTE: Do not wait for confirmation
        tx = ACCOUNT.transfer(address, amount, gas_limit=gas_limit, required_confirmations=None)
        return FaucetResponse(
            txn_hash=tx.txn_hash,
            txn_url=(
                provider.network.explorer.get_transaction_url(tx.txn_hash)
                if provider.network.explorer
                else None
            ),
            balance=provider.get_balance(address),
        )

token_list_source_uri = "https://gateway.ipfs.io/ipns/tokens.uniswap.org"

# Create an instance of TokenListManager and install the 1inch token list
tlm = TokenListManager()
tlm.install_tokenlist(token_list_source_uri)


@app.get("/token-list/{chain_id}")
def token_list(chain_id: int):
    """
    Gets list of tokens
    """
    # Get tokens (you can customize this with parameters if needed)
    tokens = tlm.get_tokens(token_listname="Uniswap Labs Default", chain_id=chain_id)
    # Convert the filter object to a list
    tokens_ls = list(tokens)
    # Convert the list to json and return
    token_ls = [ls.dict() for ls in tokens_ls]
    return json.dumps(token_ls)


@app.get("/transfer-token/{chain_id}/{impersonated_account}")
def transfer_token(chain_id: int, impersonated_account: str):
    """
    transfers tokens
    """

    """ impersonate account and token transfer from that account"""
    anvil_address = "http://127.0.0.1:8545" #TODO: update to environment variable
    with networks.ethereum.mainnet.use_provider(anvil_address) as provider:
        assert chain_id == provider.chain_id
        response = chain.provider._make_request("anvil_impersonateAccount", [impersonated_account])
        acct = ImpersonatedAccount(raw_address=impersonated_account)
        return acct.balance
    
# @app.get("/token-transfer/{token_address}/{chain_id}")
# def token_transfer(token_address: AddressType, chain_id: int):
#     """impersonate account and token transfer from that account"""
#     chain.provider._make_request(
#         "anvil_impersonateAccount", ["0x38225DE2EDa59e37b4B452c904fe21c507bbE4fa"]
#     )
#     acct = ImpersonatedAccount(raw_address="0x38225DE2EDa59e37b4B452c904fe21c507bbE4fa")
#     return acct.balance

#     # account = accounts["example.eth"]
#     # account.transfer()
#     # return "method not implemented"


@app.exception_handler(ApeException)
async def ape_exception_handler(request: Request, exc: ApeException):
    return JSONResponse(status_code=400, content=dict(error=str(exc)))


# NOTE: must come after any routes, to ensure the fallthrough works properly
app.mount("/", StaticFiles(directory=(Path(__file__).parent / "web"), html=True), name="app")


def start():
    """
    Launch app
    """
    uvicorn.run("faucet.app:app", reload=True, reload_dirs=["faucet/"])
