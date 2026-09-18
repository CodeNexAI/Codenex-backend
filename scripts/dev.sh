#!/usr/bin/env sh
set -eu

uvicorn app.main:app --reload
