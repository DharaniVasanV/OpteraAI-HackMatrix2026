"""
AgentOS — Document Agent Entry Point
Usage:
    python main.py                        # runs built-in demo
    python main.py search "<query>"       # searches the local index
    python main.py process "<text>"       # processes raw text input
"""
import json
import sys
from document_agent import process, search_index


def main():
    args = sys.argv[1:]

    if not args:
        # Demo mode
        sample = """
        Subject: Internship Offer Letter - Amazon SDE Intern 2025

        Congratulations! Please download your offer letter from the link below.
        Offer Letter: https://amazon.jobs/downloads/offer_letter_2025.pdf
        Joining Date: 15/08/2025
        Stipend: INR 80,000/month
        Contact HR: hr-intern@amazon.com
        Apply / Accept Offer: https://amazon.jobs/accept?token=abc123
        Deadline to accept: 10/07/2025
        """
        result = process(sample, auto_download=False)
        print(json.dumps(result, indent=2))
        return

    command = args[0].lower()

    if command == "search" and len(args) >= 2:
        results = search_index(args[1])
        print(json.dumps(results, indent=2))

    elif command == "process" and len(args) >= 2:
        result = process(args[1], auto_download="--auto" in args)
        print(json.dumps(result, indent=2))

    else:
        print("Usage: python main.py [search <query> | process <text> [--auto]]")
        sys.exit(1)


if __name__ == "__main__":
    main()
