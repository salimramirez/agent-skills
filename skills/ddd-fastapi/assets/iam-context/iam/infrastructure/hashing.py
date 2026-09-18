"""Password hashing with Argon2, through pwdlib."""
import asyncio

from pwdlib import PasswordHash

from iam.application.outbound_services import HashingService


class Argon2HashingService(HashingService):
    """Hashes passwords with Argon2id, pwdlib's recommended algorithm.

    Hashing is deliberately slow CPU work. Run on the event loop it would stall
    every other request for its whole duration, so both methods hand it to a
    worker thread.
    """

    def __init__(self) -> None:
        """Initialize the hasher with pwdlib's recommended parameters."""
        self._hasher = PasswordHash.recommended()

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hasher.hash, password)

    async def verify(self, password: str, password_hash: str) -> bool:
        return await asyncio.to_thread(self._hasher.verify, password, password_hash)
