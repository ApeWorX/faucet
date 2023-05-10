import json
import os
from pathlib import Path
from typing import Annotated

import uvicorn
from ape import networks
from ape_accounts import KeyfileAccount
from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from pydantic import AnyUrl, BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if account_json := os.environ.get("ACCOUNT_JSON"):
    path = Path(__file__).parent / "bot.json"
    path.write_text(account_json)

ACCOUNT = KeyfileAccount(keyfile_path=(Path(__file__).parent / "bot.json"))
ACCOUNT.set_autosign(True, passphrase="anvil")  # NOTE: Bundle account keyfile when building

FAUCET_LIMIT = int(os.environ.get("FAUCET_TRANSFER_LIMIT", 10**18))

NETWORK_TRIPLE = os.environ.get("FAUCET_RPC_ADDRESS", "http://localhost:8545")


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
            balance=provider.get_balance(address) + amount,
        )


# NOTE: must come after any routes, to ensure the fallthrough works properly
app.mount("/", StaticFiles(directory=(Path(__file__).parent / "web")), name="app")


def start():
    """
    Launch app
    """
    uvicorn.run("faucet.app:app", reload=True, reload_dirs=["faucet/"])
