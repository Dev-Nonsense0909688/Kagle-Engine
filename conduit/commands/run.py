from conduit.runtime.inference import Engine
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from conduit.chatml_templates import chat_prompt
from conduit.commands.path import CONFIG_DIR
import os


console = Console()

file = os.path.join(CONFIG_DIR, "system.prompt")




def run(args):
    if not args:
        console.print("[red] Oops! [/red]")
        return

    model = args[0]  
    
    if os.path.exists(file) and os.path.getsize(file) != 0:
        system = open(file, "r").read()
    else:
        system = f"""
        Your AI Model or brain is: {model}
        You are upgraded by Aurora Labs
        You are a over-expressive AI Assistant.
        
        You are helpful to the user. 
        """
           
    engine = Engine(model)

    try:
        while True:

            inp = console.input("[bold cyan]>>> [/bold cyan]")
            prompt = inp

            response = ""
            spinner = Spinner("dots", text="Thinking...")

            with Live(spinner, console=console, refresh_per_second=20) as live:
                first_token = True

                prompt = chat_prompt(system=system, user=prompt)
                try:
                    for token in engine.generate(prompt):

                        if first_token:
                            first_token = False
                            live.update(Markdown(""))

                        response += token
                        live.update(Markdown(response))

                except KeyboardInterrupt:
                    continue

    except KeyboardInterrupt:
        console.print("\n[yellow]bye.[/yellow]")
