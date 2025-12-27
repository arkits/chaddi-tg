#!/bin/bash
# Run all tests with coverage

uv run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
