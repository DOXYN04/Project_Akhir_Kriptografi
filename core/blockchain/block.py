"""
core/blockchain/block.py — Struktur blok blockchain sederhana.
"""

import hashlib
import json
import time
import hmac
from dataclasses import dataclass, field


@dataclass
class Block:
    """Satu blok dalam rantai aset."""
    index: int
    timestamp: float
    data: dict          # {"asset_id","asset_name","sha256","action","owner_sig"}
    prev_hash: str
    nonce: int = 0
    hash: str = field(default="", repr=False)

    def compute_hash(self) -> str:
        """
        Hitung SHA-256 atas (index|timestamp|data_json|prev_hash|nonce).
        data_json menggunakan sort_keys=True agar deterministik.
        """
        data_json = json.dumps(self.data, sort_keys=True, ensure_ascii=False)
        content = (
            f"{self.index}|{self.timestamp}|{data_json}|{self.prev_hash}|{self.nonce}"
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        """Serialisasi blok ke dict (untuk simpan ke DB)."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data_json": json.dumps(self.data, sort_keys=True, ensure_ascii=False),
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Block":
        """Muat blok dari dict (hasil query DB)."""
        block = cls(
            index=d["index"] if "index" in d else d["idx"],
            timestamp=d["timestamp"],
            data=json.loads(d["data_json"]),
            prev_hash=d["prev_hash"],
            nonce=d["nonce"],
        )
        block.hash = d["hash"]
        return block
