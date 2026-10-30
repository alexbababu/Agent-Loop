# Agent Loop from Scratch & LangChain

Lern- und Demoprojekt zum Verstaendnis von agentischen Schleifen (Agent Loops), Tool Calling und Fehlerbehandlung in Python.

## Uebersicht

- `main.py`: Manuell implementierte Agent-Loop von Grund auf mit dem `openai`-SDK (OpenRouter).
  - Explizites JSON-Schema fuer Tools
  - Manuelle Dispatch-Tabelle
  - Eigene `for`-Schleife fuer Denk-Schritte
  - Fehlerabfangung und Selbstkorrektur ueber Tool-Rückmeldungen
  - Interaktiver CLI-Chat (`while True`)

- `main2.py`: Aequivalente Implementierung mit LangChain.
  - `@tool`-Decorator zur automatischen Schema-Erstellung
  - `ToolException` und `handle_tool_error = True` zur Fehlerbehandlung
  - `create_agent` fuer den internen Agent-Graphen
  - Gleicher interaktiver CLI-Chat-Ablauf

## Voraussetzungen

- Python >= 3.11
- Paketmanager `uv`
- OpenRouter API-Key

## Einrichtung

1. Umgebungsvariablen anlegen:
   ```bash
   cp .env.example .env
   ```
2. `OPENROUTER_API_KEY` in der Datei `.env` eintragen.

## Ausfuehrung

Aufgrund von NAS-Mounts mit `noexec` ueber das Wrapper-Skript starten:

```bash
# From-Scratch Variante
bash run.sh main.py

# LangChain Variante
bash run.sh main2.py
```
