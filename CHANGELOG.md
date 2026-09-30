# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-09-30

### Features

- Python/FastAPI x402 payment wrapper with reverse proxy
- Two Kite networks: mainnet (USDC.e) and testnet (pieUSD)
- `$0.001`-style price parser with EIP-3009 support
- Payment middleware: unpaid requests return 402 + `PAYMENT-REQUIRED` header
- Health-check endpoint (`/healthz`)
- CORS support (optional)
- Dockerfile for production deployment
- CI/CD: lint (ruff, mypy) + test (pytest, 19 tests)
- Pre-commit hooks: ruff, mypy, typos, file checks
- CHANGELOG via git-cliff
