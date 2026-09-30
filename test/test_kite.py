"""Tests for kite.py — Kite chain configuration and money parser (extended)."""

import sys

sys.path.insert(0, ".")

import pytest
from x402.schemas import AssetAmount

from kite import (
    FACILITATOR_URL,
    KITE_MAINNET,
    KITE_TESTNET,
    kite_chain_by_name,
    kite_money_parser,
)


class TestKiteConfig:
    def test_mainnet_chain_id(self):
        assert KITE_MAINNET.chain_id == 2366

    def test_testnet_chain_id(self):
        assert KITE_TESTNET.chain_id == 2368

    def test_mainnet_network_caip(self):
        assert KITE_MAINNET.network == "eip155:2366"

    def test_testnet_network_caip(self):
        assert KITE_TESTNET.network == "eip155:2368"

    def test_mainnet_asset_symbol(self):
        assert KITE_MAINNET.asset_symbol == "USDC.e"

    def test_testnet_asset_symbol(self):
        assert KITE_TESTNET.asset_symbol == "pieUSD"

    def test_asset_decimals(self):
        assert KITE_MAINNET.asset_decimals == 6
        assert KITE_TESTNET.asset_decimals == 18

    def test_asset_addresses_differ(self):
        assert KITE_MAINNET.asset_address != KITE_TESTNET.asset_address

    def test_rpc_urls_differ(self):
        assert KITE_MAINNET.rpc_url != KITE_TESTNET.rpc_url

    def test_facilitator_url(self):
        assert KITE_MAINNET.facilitator_url == FACILITATOR_URL
        assert KITE_TESTNET.facilitator_url == FACILITATOR_URL

    def test_frozen_dataclass(self):
        with pytest.raises(AttributeError):
            KITE_MAINNET.asset_decimals = 99  # type: ignore


class TestKiteChainByName:
    def test_default_mainnet(self):
        chain = kite_chain_by_name(None)
        assert chain.network == "eip155:2366"

    def test_empty_string_mainnet(self):
        chain = kite_chain_by_name("")
        assert chain.network == "eip155:2366"

    def test_explicit_mainnet(self):
        chain = kite_chain_by_name("mainnet")
        assert chain.asset_symbol == "USDC.e"

    def test_explicit_testnet(self):
        chain = kite_chain_by_name("testnet")
        assert chain.asset_symbol == "pieUSD"

    def test_case_insensitive(self):
        chain = kite_chain_by_name("TestNet")
        assert chain.network == "eip155:2368"

    def test_whitespace_trimmed(self):
        chain = kite_chain_by_name("  mainnet  ")
        assert chain.network == "eip155:2366"

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="unknown KITE_NETWORK"):
            kite_chain_by_name("invalid")


class TestMoneyParser:
    def setup_method(self):
        self.chain_testnet = kite_chain_by_name("testnet")
        self.chain_mainnet = kite_chain_by_name("mainnet")
        self.parse_testnet = kite_money_parser(self.chain_testnet)
        self.parse_mainnet = kite_money_parser(self.chain_mainnet)

    # ---- Return type ----

    def test_returns_asset_amount_testnet(self):
        result = self.parse_testnet(0.001, self.chain_testnet.network)
        assert isinstance(result, AssetAmount)

    def test_returns_asset_amount_mainnet(self):
        result = self.parse_mainnet(1.0, self.chain_mainnet.network)
        assert isinstance(result, AssetAmount)

    # ---- Dollar prefix handling ----

    def test_dollar_prefix_testnet(self):
        result = self.parse_testnet("$0.001", self.chain_testnet.network)
        assert isinstance(result, AssetAmount)
        assert int(result.amount) > 0

    def test_dollar_prefix_mainnet(self):
        result = self.parse_mainnet("$1.00", self.chain_mainnet.network)
        assert isinstance(result, AssetAmount)
        assert int(result.amount) > 0

    # ---- Network filtering ----

    def test_none_for_wrong_network(self):
        result = self.parse_testnet(0.001, "eip155:1")
        assert result is None

    def test_returns_none_for_other_chain(self):
        result = self.parse_mainnet(0.001, self.chain_testnet.network)
        assert result is None

    # ---- Validation ----

    def test_zero_rejected(self):
        with pytest.raises(ValueError, match="price must be positive"):
            self.parse_testnet(0, self.chain_testnet.network)

    def test_negative_rejected(self):
        with pytest.raises(ValueError, match="price must be positive"):
            self.parse_testnet(-1, self.chain_testnet.network)

    def test_string_zero_rejected(self):
        with pytest.raises(ValueError, match="price must be positive"):
            self.parse_testnet("0", self.chain_testnet.network)

    def test_nan_rejected(self):
        with pytest.raises((ValueError, pytest.skip.Exception)):
            self.parse_testnet("not-a-number", self.chain_testnet.network)

    def test_below_minimum_unit_rejected(self):
        """1e-19 pieUSD is below 1 atomic unit (1e-18)."""
        with pytest.raises(ValueError, match="below one unit"):
            self.parse_testnet(0.0000000000000000001, self.chain_testnet.network)

    # ---- Atomic unit calculations ----

    def test_atomic_units_testnet(self):
        result = self.parse_testnet(0.001, self.chain_testnet.network)
        # 0.001 pieUSD = 0.001 * 10^18 = 10^15 atoms
        assert int(result.amount) == 10**15

    def test_atomic_units_mainnet(self):
        result = self.parse_mainnet(1.0, self.chain_mainnet.network)
        # 1.0 USDC.e = 1.0 * 10^6 = 10^6 atoms
        assert int(result.amount) == 10**6

    def test_precise_atomic_calculation(self):
        result = self.parse_testnet("1.5", self.chain_testnet.network)
        expected = int(1.5 * 10**18)
        assert int(result.amount) == expected

    # ---- Asset address ----

    def test_asset_address_testnet(self):
        result = self.parse_testnet(0.001, self.chain_testnet.network)
        assert result.asset == self.chain_testnet.asset_address

    def test_asset_address_mainnet(self):
        result = self.parse_mainnet(1.0, self.chain_mainnet.network)
        assert result.asset == self.chain_mainnet.asset_address

    # ---- EIP-712 extras ----

    def test_eip712_extras_present_testnet(self):
        result = self.parse_testnet(0.001, self.chain_testnet.network)
        assert result.extra is not None
        assert result.extra["name"] == "pieUSD"
        assert result.extra["version"] == "1"

    def test_eip712_extras_present_mainnet(self):
        result = self.parse_mainnet(1.0, self.chain_mainnet.network)
        assert result.extra is not None
        assert result.extra["name"] == "Bridged USDC (Kite AI)"
        assert result.extra["version"] == "2"
