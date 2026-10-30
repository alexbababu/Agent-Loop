import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Laedt Umgebungsvariablen aus der .env Datei
load_dotenv()

# Schritt 1: Ein Werkzeug (Tool) definieren
# Ein Tool fuer einen Agenten ist zunaechst eine ganz normale Python-Funktion.


def get_weather(location: str) -> str:
    """Gibt Wetterdaten fuer einen angegebenen Ort zurueck."""
    # In der Praxis wuerde hier eine echte Wetter-API aufgerufen.
    # Fuer unseren Test genuegt ein simuliertes Ergebnis:
    return f"In {location} ist es sonnig bei 21 Grad Celsius."


def calculate(expression: str) -> str:
    """Berechnet einen mathematischen Ausdruck und gibt das Ergebnis zurueck."""
    try:
        # Aus Sicherheitsgruenden ohne Zugriff auf Python-Builtins:
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Fehler bei Berechnung: {e}"


# Schritt 2: Das Tool dem LLM beschreiben (Tool-Schema / JSON-Schema)
# Das LLM kann unseren Python-Code nicht direkt einsehen.
# Wir muessen ihm im OpenAI/OpenRouter-Format erklaeren:
# - Wie heisst die Funktion?
# - Was macht sie (description)?
# - Welche Argumente erwartet sie (parameters)?
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Gibt das aktuelle Wetter fuer einen bestimmten Ort zurueck.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Der Name der Stadt, z. B. Berlin, Muenchen, Tokio",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Berechnet einen mathematischen Ausdruck (z. B. '21 * 1.8 + 32').",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Der mathematische Ausdruck als String.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]


# Schritt 3: Die Tool-Registry (Dispatch-Tabelle)
# Das LLM liefert uns spaeter nur Text zurueck, z. B. den String "get_weather".
# Python weiss nicht automatisch, welche Funktion damit gemeint ist.
# Wir erstellen ein Dictionary, das den Namen auf die echte Python-Funktion abbildet:
available_tools = {
    "get_weather": get_weather,
    "calculate": calculate,
}


# Schritt 4: Client und Gedaechtnis (Message-History) aufsetzen
# LLMs sind zustandslos (stateless). Sie erinnern sich an keinen vorherigen Aufruf.
# Das gesamte "Gedaechtnis" unseres Agenten ist eine Python-Liste von Nachrichten (messages).
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
MAX_ITERATIONS = 5

SYSTEM_PROMPT = (
    "Du bist ein praeziser Assistent. Antworte immer auf Deutsch und fasse dich kurz. "
    "Fuehre alle mathematischen Berechnungen ausnahmslos mit dem calculate-Tool durch."
)

# Das Gedaechtnis startet mit den festen Verhaltensregeln an Position 0:
messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

print("Agent ist bereit! Tippe deine Frage ein ('q' oder 'exit' zum Beenden).\n")

# Schritt 5: Die aeussere Chat-Schleife (wartet auf Benutzereingaben)
while True:
    try:
        user_input = input("Du: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nAuf Wiedersehen!")
        break

    if not user_input:
        continue

    if user_input.lower() in ("exit", "quit", "q"):
        print("Auf Wiedersehen!")
        break

    # Neue Benutzereingabe ins Gedaechtnis aufnehmen:
    messages.append({"role": "user", "content": user_input})

    # Schritt 5b: Die innere Denk-Schleife (Agent Loop fuer diesen Chat-Schritt)
    for iteration in range(MAX_ITERATIONS):
        print(f"--- Denk-Schritt {iteration + 1} ---")

        # 1. Aktuelle Historie und Tools an das Modell senden
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
        )

        response_message = response.choices[0].message

        # 2. Antwort des Modells in das Gedaechtnis aufnehmen
        messages.append(response_message)

        # 3. Pruefen: Ist das Modell fertig?
        if not response_message.tool_calls:
            print(f"\nAgent: {response_message.content}\n")
            break

        print(f"Modell moechte Werkzeuge aufrufen: {len(response_message.tool_calls)} Tool-Call(s)")

        # Schritt 6: Die angeforderten Werkzeuge lokal ausfuehren (mit Fehlerabfangung)
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name

            try:
                # 1. Argumente parsen
                tool_args = json.loads(tool_call.function.arguments)
                print(f"-> Fuehre Tool aus: '{tool_name}' mit Argumenten: {tool_args}")

                # 2. Pruefen, ob das Modell ein existierendes Werkzeug gewaehlt hat
                if tool_name not in available_tools:
                    raise ValueError(
                        f"Unbekanntes Werkzeug '{tool_name}'. "
                        f"Verfuegbare Werkzeuge sind: {list(available_tools.keys())}"
                    )

                tool_function = available_tools[tool_name]

                # 3. Funktion aufrufen
                tool_result = tool_function(**tool_args)
                print(f"-> Ergebnis erhalten: '{tool_result}'")

            except Exception as e:
                tool_result = f"Fehler bei Ausfuehrung von '{tool_name}': {e}"
                print(f"-> FEHLER abgefangen und an Modell uebergeben: '{tool_result}'")

            # Das Ergebnis verknuepfen wir ueber tool_call.id mit der Anfrage:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result),
                }
            )
