import os
import json
import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.markdown import Markdown

# Initialize rich console
console = Console()

def load_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    return {
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "GOOGLE_AI_STUDIO_KEY": os.getenv("GOOGLE_AI_STUDIO_KEY")
    }

def create_payload(model: str, messages: list) -> dict:
    return {
        "model": model,
        "messages": messages,
        "stream": True
    }

def stream_response(client: httpx.Client, url: str, headers: dict, payload: dict, engine_name: str) -> str:
    """Streams the response from the API and updates the Rich Live display."""
    full_response = ""
    
    with httpx.stream("POST", url, headers=headers, json=payload, timeout=30.0) as response:
        response.raise_for_status()
        
        with Live(Panel("...", title=f"[bold cyan]Nexus[/] | Engine: [yellow]{engine_name}[/]", border_style="cyan"), console=console, refresh_per_second=15) as live:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        # Groq and Gemini (OpenAI compatible) return chunks in this format
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                chunk = delta["content"]
                                full_response += chunk
                                # Update the live display
                                live.update(Panel(Markdown(full_response), title=f"[bold cyan]Nexus[/] | Engine: [yellow]{engine_name}[/]", border_style="cyan"))
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass
    return full_response

def chat_loop():
    console.print(Panel("[bold green]Welcome to Nexus-CLI[/]\nType your message below. Type 'exit' or 'quit' to close.", title="System", border_style="green"))
    
    keys = load_environment()
    
    if not keys["GROQ_API_KEY"]:
        console.print("[bold yellow]Warning:[/] GROQ_API_KEY is not set in .env")
    if not keys["GOOGLE_AI_STUDIO_KEY"]:
        console.print("[bold yellow]Warning:[/] GOOGLE_AI_STUDIO_KEY is not set in .env")

    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL = "llama-3.3-70b-versatile"

    GOOGLE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    GOOGLE_MODEL = "gemini-1.5-flash"

    messages = [{"role": "system", "content": "You are Nexus, a helpful AI assistant. Keep responses clear and concise."}]

    with httpx.Client() as client:
        while True:
            try:
                user_input = Prompt.ask("\n[bold blue]You[/]")
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[bold green]Session terminated. Goodbye![/]")
                    break
                if not user_input.strip():
                    continue

                messages.append({"role": "user", "content": user_input})
                
                # Attempt primary engine (Groq)
                groq_headers = {
                    "Authorization": f"Bearer {keys['GROQ_API_KEY']}",
                    "Content-Type": "application/json"
                }
                groq_payload = create_payload(GROQ_MODEL, messages)

                try:
                    if not keys["GROQ_API_KEY"]:
                        raise ValueError("GROQ_API_KEY missing")
                        
                    response_content = stream_response(
                        client, 
                        GROQ_URL, 
                        groq_headers, 
                        groq_payload, 
                        "Groq (Llama-3.3-70b)"
                    )
                    messages.append({"role": "assistant", "content": response_content})
                    
                except (httpx.HTTPStatusError, ValueError) as e:
                    # Check for failover conditions
                    is_status_error = isinstance(e, httpx.HTTPStatusError)
                    status_code = e.response.status_code if is_status_error else None
                    
                    if isinstance(e, ValueError) or status_code in [401, 429]:
                        reason = "Missing Key" if isinstance(e, ValueError) else f"HTTP {status_code}"
                        console.print(f"[bold yellow]Primary Engine Failure ({reason}). Intercepting exception and failing over to Google AI Studio...[/]")
                        
                        if not keys["GOOGLE_AI_STUDIO_KEY"]:
                            console.print("[bold red]Fatal Error:[/] Google AI Studio Key is missing. Cannot perform failover.")
                            messages.pop() # Remove user message from history
                            continue
                            
                        google_headers = {
                            "Authorization": f"Bearer {keys['GOOGLE_AI_STUDIO_KEY']}",
                            "Content-Type": "application/json"
                        }
                        google_payload = create_payload(GOOGLE_MODEL, messages)
                        
                        try:
                            response_content = stream_response(
                                client, 
                                GOOGLE_URL, 
                                google_headers, 
                                google_payload, 
                                "Google AI Studio (Gemini Fallback)"
                            )
                            messages.append({"role": "assistant", "content": response_content})
                        except Exception as fallback_error:
                            console.print(f"[bold red]Fallback Engine Error:[/] {fallback_error}")
                            messages.pop()
                    else:
                        console.print(f"[bold red]Primary Engine Error:[/] {e}")
                        messages.pop()
                        
            except KeyboardInterrupt:
                console.print("\n[bold green]Session terminated. Goodbye![/]")
                break
            except Exception as e:
                console.print(f"[bold red]Unexpected Error:[/] {e}")
                if messages and messages[-1]["role"] == "user":
                    messages.pop()

if __name__ == "__main__":
    chat_loop()
