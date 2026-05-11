#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 -m streamlit run auditoria_app.py --server.headless true
