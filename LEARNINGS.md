# Lernprotokoll: Agentic Loops von Grund auf verstehen

Dieses Dokument fasst alle bisher gelernten Konzepte, Code-Muster und Erkenntnisse zum Thema KI-Agenten und Agent Loops zusammen.

---

## 1. Das Grundprinzip: Zustandslosigkeit & Gedächtnis

- **LLMs sind stateless (zustandslos):** Sie erinnern sich an keinen früheren Aufruf.
- **Das Gedächtnis ist eine Liste:** Das gesamte "Gedächtnis" des Agenten ist einfach eine Python-Liste von Nachrichten (`messages`).
- **Rollen im OpenAI-Standard:**
  - `system`: Feste Verhaltensregeln, Persönlichkeit und Leitplanken (steht immer an Index 0).
  - `user`: Eingaben und Fragen des Benutzers.
  - `assistant`: Antworten des Sprachmodells (entweder Text oder Aufforderungen zu Tool-Calls).
  - `tool`: Rückgabewerte der lokal ausgeführten Python-Funktionen.

---

## 2. Tool Calling von Grund auf (`main.py`)

Um einem LLM Werkzeuge zu geben, braucht es in reinem Python drei Bausteine:

1. **Die Python-Funktion:** Die eigentliche Logik (z. B. `get_weather` oder `calculate`).
2. **Das JSON-Schema (`tools`):** Eine maschinenlesbare Beschreibung für das LLM:
   - Wie heißt die Funktion?
   - Was macht sie (`description`)?
   - Welche Parameter mit welchen Datentypen erwartet sie (`parameters`)?
3. **Die Dispatch-Tabelle (`available_tools`):** Ein Python-Dictionary (`{"get_weather": get_weather}`), um den Textnamen des Modells auf die echte Python-Funktion zu mappen.

---

## 3. Multi-Tool & Parallele Aufrufe

- **Dynamische Auswahl:** Stehen mehrere Werkzeuge in der `tools`-Liste, wählt das Modell situativ das passende Werkzeug aus.
- **Parallele Tool-Calls:** Braucht das Modell mehrere Werkzeuge auf einmal (z. B. Wetter für zwei Städte gleichzeitig), liefert die API mehrere Calls in einem einzigen Denk-Schritt.
- **Die `tool_call_id`:** Jeder Tool-Call erhält eine eindeutige ID. Das Ergebnis muss mit genau dieser ID zurückgesendet werden, damit das Modell weiß, welches Ergebnis zu welcher Anfrage gehört.

---

## 4. Fehlerbehandlung & Selbstkorrektur (Self-Correction)

Ein Agent darf bei Fehlern nicht abstürzen. Wir unterscheiden zwei Ebenen:

1. **Ebene 1 (Im Werkzeug):** Fachliche Fehler (z. B. Division durch Null in Mathe-Funktionen).
2. **Ebene 2 (In der Loop):** Schnittstellenfehler (z. B. kaputtes JSON des LLMs, falsche Argumentnamen oder ein halluzinierter Tool-Name).

### Das Selbstkorrektur-Prinzip:
Fehler werden per `try...except` abgefangen und **als Text an das Modell zurückgeschickt** (`role: "tool"`).
- Das Modell liest die Fehlermeldung im nächsten Denk-Schritt.
- Es versteht, was schiefgelaufen ist.
- Es korrigiert seine Parameter oder wählt eine Alternative, ohne dass das Programm abstürzt.

---

## 5. Das Framework-Gegenstück mit LangChain (`main2.py`)

LangChain abstrahiert die manuelle Schleife in fertige Komponenten:

| Konzept | Manuell (`main.py`) | LangChain (`main2.py`) |
| :--- | :--- | :--- |
| **Tool-Definition** | Funktion + JSON-Schema + Dispatch-Dict | `@tool` Decorator |
| **Fehlerbehandlung** | Eigener `try...except`-Block in der `for`-Loop | `raise ToolException(...)` und `handle_tool_error = True` |
| **Schleife / ReAct** | Eigene `for iteration in range(MAX_ITERATIONS)` | `agent = create_agent(llm, tools)` |
| **System-Prompt** | Manuell an Index 0 in `messages` | Parameter `system_prompt="..."` in `create_agent` |

---

## 6. Die interaktive Chat-Schleife (Zwei Schleifen)

Ein echter Chat-Agent benötigt zwei ineinander verschachtelte Schleifen:

1. **Äußere Schleife (`while True:`):**
   - Wartet auf Benutzereingaben im Terminal (`input("Du: ")`).
   - Hängt die neue Benutzerfrage an die bestehende `messages`-Liste an.
   - Beendet das Programm bei `exit` oder `q`.
2. **Innere Schleife (`for iteration in range(MAX_ITERATIONS)` bzw. `agent.invoke`):**
   - Der eigentliche ReAct-Denkprozess.
   - Ruft Werkzeuge auf, bis das Modell eine finale Textantwort ohne weitere Tool-Calls liefert.
   - Kehrt danach automatisch zur äußeren Schleife zurück.

---

## 7. Projekt- & Systempraxis

- **Sicherheit:** Sensible API-Keys gehören in `.env` und werden zwingend über `.gitignore` vom Git-Repository ausgeschlossen.
- **Git-Konvention:** Saubere, atomare Commits im Format `Conventional Commits` (`feat(...)`, `docs(...)`).
- **NAS & Dateisysteme:** Bei Netzwerkfreigaben mit `noexec`-Mounts können Skripte nicht direkt per `./script.sh` gestartet werden; stattdessen wird der Interpreter explizit aufgerufen (`bash script.sh`).
