import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import ToolException, tool
from langchain_openai import ChatOpenAI

load_dotenv()


# Schritt 1 in LangChain: Der @tool Decorator
# Fasst Funktion, JSON-Schema und Registry in einem zusammen.
@tool
def get_weather(location: str) -> str:
    """Gibt das aktuelle Wetter fuer einen bestimmten Ort zurueck."""
    return f"In {location} ist es sonnig bei 21 Grad Celsius."


@tool
def calculate(expression: str) -> str:
    """Berechnet einen mathematischen Ausdruck und gibt das Ergebnis zurueck."""
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        # In LangChain signalisieren wir einen Tool-Fehler mit ToolException:
        raise ToolException(f"Fehler bei Berechnung: {e}")


# Dieses Flag weist LangChain an, ToolException abzufangen und als
# Fehlernachricht an das LLM weiterzugeben (statt das Programm zu crashen):
calculate.handle_tool_error = True


tools = [get_weather, calculate]


# Schritt 2 in LangChain: Modell konfigurieren
llm = ChatOpenAI(
    model="nvidia/nemotron-3-ultra-550b-a55b:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


SYSTEM_PROMPT = (
    "Du bist ein praeziser Assistent. Antworte immer auf Deutsch und fasse dich kurz. "
    "Fuehre alle mathematischen Berechnungen ausnahmslos mit dem calculate-Tool durch."
)

# Schritt 3 in LangChain: Die Schleife (Agenten-Loop) erstellen
# LangChain nimmt den system_prompt direkt als Parameter entgegen:
agent = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)

# Das Gedaechtnis startet leer:
messages = []

print("Agent (LangChain) bereit! Tippe deine Frage ein ('q' oder 'exit' zum Beenden).\n")

# Schritt 4: Die aeussere Chat-Schleife (wartet auf Benutzereingaben)
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
    vorherige_laenge = len(messages)

    # agent.invoke fuehrt die innere Agent-Loop automatisch komplett durch:
    response = agent.invoke({"messages": messages})

    # Das Gedaechtnis mit allen neuen Nachrichten aktualisieren:
    messages = response["messages"]

    # Zwischenschritte (Tool-Aufrufe) dieser Runde anzeigen:
    neue_schritte = messages[vorherige_laenge:]
    for msg in neue_schritte:
        if msg.type == "ai" and getattr(msg, "tool_calls", None):
            for call in msg.tool_calls:
                print(f"-> Modell ruft Tool auf: '{call['name']}' mit: {call['args']}")
        elif msg.type == "tool":
            print(f"-> Ergebnis aus Python: {msg.content}")

    # Die finale Antwort ist immer die letzte Nachricht:
    print(f"\nAgent: {messages[-1].content}\n")

