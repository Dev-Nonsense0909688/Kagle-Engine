import time
from conduit.runtime.inference import Engine
from rich.console import Console
from rich.table import Table

console = Console()

PROMPT = "Write a 2000 token story about a dragon and a hacker."

def run(args):
    if not args:
        console.print("[red] Oops! [/red]")
        return

    console.print("[bold cyan]Starting model benchmark...[/bold cyan]\n")

    start_load = time.time()

    engine = Engine(args[0])
    load_time = time.time() - start_load

    console.print(f"[green]Model load time:[/green] {load_time:.3f}s")

    tokens = 0
    first_token_time = None
    output = ""
    print("-"*40+" Tokens generated "+"-"*40)
    start = time.time()
    for token in engine.generate(PROMPT):
        if tokens == 0:
            first_token_time = time.time()

        print(token, end="", flush=True)

        output += token
        tokens += 1

    end = time.time()

    total_time = end - start
    first_token_latency = first_token_time - start

    tps = tokens / (total_time - first_token_latency)  # tokens/sec = tokens / (total_time - first_token_latency)

    table = Table(title="Benchmark Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Unique Words used ", f"{set(output).__len__()}")
    table.add_row("First Token Latency", f"{first_token_latency:.3f}s")
    table.add_row("Total Generation Time", f"{total_time:.3f}s")
    table.add_row("Tokens Generated", str(tokens))
    table.add_row("Tokens/sec", f"{tps:.2f}")

    console.print()
    console.print(table)
