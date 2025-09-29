import argparse
from agent import Agent

def main():
    parser = argparse.ArgumentParser(description="AI Agent CLI")
    parser.add_argument("--task", required=True, help="Tarea a ejecutar por el agente")
    parser.add_argument("--max-steps", type=int, default=5, help="Máximo de iteraciones del agente")
    args = parser.parse_args()

    agent = Agent(max_steps=args.max_steps)
    out = agent.run(args.task)
    print(out)

if __name__ == "__main__":
    main()
