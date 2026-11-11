"""
core/blockchain/chain.py — Rantai blok: genesis, PoW, validasi, persist ke DB.

Setiap blok menyertakan tanda tangan HMAC-SHA256 atas data sebagai bukti kepemilikan.
"""

import hashlib
import hmac
import json
import time
from typing import Optional

import config
from core.auth.kdf import hkdf_derive
from core.blockchain.block import Block
from core.db import models as db


def _owner_sig(data: dict, master_key: bytes) -> str:
    """Tanda tangan HMAC-SHA256 atas data dict dengan kunci turunan master_key."""
    sign_key = hkdf_derive(master_key, b"blockchain-sign", 32)
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hmac.new(sign_key, payload, hashlib.sha256).hexdigest()


class Blockchain:
    """Rantai blok single-node tamper-evident untuk aset penting."""

    def __init__(self, master_key: bytes, difficulty: int = config.POW_DIFFICULTY):
        self.master_key = master_key
        self.difficulty = difficulty
        self.chain: list[Block] = []
        self._load_from_db()
        if not self.chain:
            self._create_genesis()

    # ── Inisialisasi ───────────────────────────────────────────────────────────

    def _create_genesis(self) -> None:
        genesis = Block(
            index=0,
            timestamp=time.time(),
            data={"info": "Genesis Block"},
            prev_hash="0" * 64,
        )
        genesis.hash = genesis.compute_hash()
        self.chain.append(genesis)
        db.save_block(genesis.to_dict())

    def _load_from_db(self) -> None:
        rows = db.load_blocks()
        self.chain = [Block.from_dict(r) for r in rows]

    # ── Mining (PoW) ───────────────────────────────────────────────────────────

    def _mine(self, block: Block) -> Block:
        """Cari nonce hingga hash memenuhi target difficulty."""
        target = "0" * self.difficulty
        block.nonce = 0
        block.hash = block.compute_hash()
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block

    # ── Tambah Aset ───────────────────────────────────────────────────────────

    def add_asset(
        self,
        name: str,
        content: bytes,
        action: str = "register",
        asset_id: Optional[str] = None,
    ) -> Block:
        """
        Hitung SHA-256 aset, tanda tangani dengan HMAC, dan tambah blok baru.
        Kembalikan blok yang telah ditambang.
        """
        sha = hashlib.sha256(content).hexdigest()
        aid = asset_id or sha[:16]
        data = {
            "asset_id":   aid,
            "asset_name": name,
            "sha256":     sha,
            "action":     action,
            "owner_sig":  _owner_sig(
                {"asset_id": aid, "sha256": sha}, self.master_key
            ),
        }
        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            data=data,
            prev_hash=self.chain[-1].hash,
        )
        block = self._mine(block)
        self.chain.append(block)
        db.save_block(block.to_dict())
        return block

    # ── Validasi ──────────────────────────────────────────────────────────────

    def is_valid(self) -> tuple[bool, list[int]]:
        """
        Validasi integritas seluruh chain.
        Kembalikan (valid?, list indeks blok bermasalah).
        """
        problems: list[int] = []
        target = "0" * self.difficulty

        for i, block in enumerate(self.chain):
            # Periksa hash sendiri
            if block.hash != block.compute_hash():
                problems.append(i)
                continue
            # Periksa PoW (kecuali genesis)
            if i > 0 and not block.hash.startswith(target):
                problems.append(i)
                continue
            # Periksa tautan prev_hash
            if i > 0 and block.prev_hash != self.chain[i - 1].hash:
                problems.append(i)

        return (len(problems) == 0, problems)

    # ── Verifikasi Aset ───────────────────────────────────────────────────────

    def verify_asset(self, content: bytes) -> Optional[Block]:
        """
        Cari hash aset dalam chain.
        Kembalikan blok pertama yang cocok, atau None bila tidak ditemukan.
        """
        sha = hashlib.sha256(content).hexdigest()
        for block in self.chain:
            if block.data.get("sha256") == sha:
                return block
        return None

    # ── Helper ────────────────────────────────────────────────────────────────

    def last_hash(self) -> str:
        return self.chain[-1].hash if self.chain else "0" * 64

    def __len__(self) -> int:
        return len(self.chain)
