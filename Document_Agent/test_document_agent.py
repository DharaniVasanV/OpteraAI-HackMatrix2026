import unittest

from document_agent import process, search_index


class DocumentAgentTests(unittest.TestCase):
    def setUp(self):
        from db import clear_documents
        clear_documents()

    def test_process_returns_structured_json_for_document_input(self):
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

        self.assertTrue(result["document_found"])
        self.assertEqual(result["document_name"], "offer_letter_2025.pdf")
        self.assertIn("Offer Letters", result["category"])
        self.assertEqual(result["priority"], "Emergency")
        self.assertIn("Download", result["recommended_actions"])
        self.assertIn("Priority Agent", result["required_agents"])

    def test_search_index_returns_results_for_known_terms(self):
        sample = """
        Subject: Smart India Hackathon 2025 - Registration Open

        Download Problem Statement: https://sih.gov.in/downloads/problem_statement_2025.pdf
        Download Rulebook: https://sih.gov.in/downloads/rulebook_2025.pdf
        Register here: https://sih.gov.in/register
        Deadline: 30/07/2025
        Prize Pool: INR 1,00,000
        """
        process(sample, auto_download=False)
        results = search_index("hackathon")
        self.assertTrue(results)


if __name__ == "__main__":
    unittest.main()
