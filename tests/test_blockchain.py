"""
tests/test_blockchain.py — Unit test blockchain sederhana.
"""

import os
import pytest
from core.blockchain.chain import Blockchain
from core.blockchain.block import Block


MASTER_KEY = os.urandom(32)


def make_chain() -> Blockchain:
    """Buat blockchain segar (menggunakan DB sementara)."""
    import config
    config.DB_PATH = ":memory:"
    # Patch save_block dan load_blocks agar menggunakan in-memory store
    import core.db.models as dbm
    _blocks = {}

    def _save(d):
        _blocks[d["index"]] = d

    def _load():
        return [_blocks[k] for k in sorted(_blocks)]

    dbm.save_block = _save
    dbm.load_blocks = _load
    return Blockchain(MASTER_KEY, difficulty=2)


class TestBlockchain:
    def test_genesis_exists(self):
        chain = make_chain()
        assert len(chain) == 1
        assert chain.chain[0].index == 0

    def test_add_asset(self):
        chain = make_chain()
        b = chain.add_asset("dok.pdf", b"isi dokumen penting")
        assert b.index == 1
        assert b.hash.startswith("00")   # difficulty=2

    def test_pow_difficulty(self):
        chain = make_chain()
        for i in range(3):
            b = chain.add_asset(f"aset{i}", os.urandom(32))
            assert b.hash.startswith("00")

    def test_is_valid_clean(self):
        chain = make_chain()
        chain.add_asset("a", b"aaa")
        chain.add_asset("b", b"bbb")
        valid, problems = chain.is_valid()
        assert valid
        assert problems == []

    def test_tamper_detected(self):
        chain = make_chain()
        chain.add_asset("x", b"original data")
        # Rusak data blok 1
        chain.chain[1].data["sha256"] = "0" * 64
        valid, problems = chain.is_valid()
        assert not valid
        assert 1 in problems

    def test_verify_asset_found(self):
        chain = make_chain()
        content = b"dokumen penting"
        chain.add_asset("doc", content)
        found = chain.verify_asset(content)
        assert found is not None
        assert found.index == 1

    def test_verify_asset_modified(self):
        chain = make_chain()
        content = b"dokumen asli"
        chain.add_asset("doc", content)
        modified = b"dokumen dimodifikasi"
        assert chain.verify_asset(modified) is None
