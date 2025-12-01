"""Main entry point for Recipe Agent CLI."""

from langchain.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agent import create_recipe_agent
from config import config

console = Console()


def _get_config_status() -> str:
    """Build configuration status lines for the startup banner."""
    lines = [f"[dim]Model:[/] [cyan]{config.model}[/]"]

    # Prompt status
    prompt_status = "[green]✓[/]" if config.prompt_file.exists() else "[red]✗[/]"
    lines.append(f"[dim]Prompt:[/] {config.prompt_file} {prompt_status}")

    # API providers
    providers = []
    if config.anthropic_api_key:
        providers.append("Anthropic")
    if config.openai_api_key:
        providers.append("OpenAI")
    if config.tavily_api_key:
        providers.append("Tavily")
    lines.append(f"[dim]APIs:[/] [green]{', '.join(providers)}[/]" if providers else "[dim]APIs:[/] [red]None[/]")

    # LangSmith
    if config.langsmith_api_key:
        lines.append(f"[dim]LangSmith:[/] [green]✓[/] {config.langsmith_project}")
    
    return "\n".join(lines)


def main():
    """Run the interactive recipe agent CLI."""
    # Display startup banner with configuration details
    console.print(Panel(
        f"[bold green]🍹 Recipe Agent Ready! 🍳[/]\n\n{_get_config_status()}\n\n[dim]Type 'quit' or 'exit' to stop.[/]",
        title="[bold]Recipe Creator[/]",
        border_style="green",
    ))

    # Create agent
    agent = create_recipe_agent()

    # Conversation history using LangChain message types
    messages: list[HumanMessage | AIMessage] = []

    # Main conversation loop
    while True:
        try:
            user_input = console.input("\n[bold blue]You:[/] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                console.print("[yellow]Goodbye! Happy cooking! 🍳[/]")
                break

            # Add user message using LangChain type
            messages.append(HumanMessage(content=user_input))

            # Invoke agent
            console.print("[dim]Thinking...[/]")
            result = agent.invoke({"messages": messages})

            # Extract and display response
            assistant_message = result["messages"][-1]
            messages.append(assistant_message)  # Already an AIMessage

            console.print("\n[bold green]Assistant:[/]")
            console.print(Markdown(assistant_message.content))

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")


if __name__ == "__main__":
    main()

