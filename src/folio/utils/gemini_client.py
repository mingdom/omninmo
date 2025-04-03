"""Google Gemini AI client for portfolio analysis."""

import logging
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google Gemini AI API."""

    def __init__(self):
        """Initialize the Gemini client with API key from environment."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set")
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro-experimental",
            generation_config=GenerationConfig(
                temperature=0.2,
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            )
        )
        logger.info("Gemini client initialized successfully")

    async def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze portfolio data using Gemini AI.

        Args:
            portfolio_data: Dictionary containing portfolio information

        Returns:
            Dictionary with structured analysis results
        """
        prompt = self._create_analysis_prompt(portfolio_data)

        try:
            response = await self.model.generate_content_async(prompt)

            # Process and structure the response
            structured_analysis = self._process_analysis_response(response.text)
            logger.info("Portfolio analysis completed successfully")
            return structured_analysis

        except Exception as e:
            logger.error(f"Error during portfolio analysis: {str(e)}")
            return {
                "error": True,
                "message": f"Analysis failed: {str(e)}",
            }

    def _create_analysis_prompt(self, portfolio_data: Dict[str, Any]) -> str:
        """
        Create a structured prompt for portfolio analysis.

        Args:
            portfolio_data: Dictionary containing portfolio information

        Returns:
            Formatted prompt string
        """
        # Extract key portfolio metrics
        positions = portfolio_data.get("positions", [])
        summary = portfolio_data.get("summary", {})

        # Format positions data
        positions_text = "\n".join([
            f"- {pos['ticker']}: {pos['position_type'].upper()}, "
            f"Value: ${pos['market_value']:.2f}, "
            f"Beta: {pos['beta']:.2f}, "
            f"Weight: {pos['weight']:.2%}"
            for pos in positions
        ])

        # Format summary data
        total_value = summary.get("total_value_net", 0)
        portfolio_beta = summary.get("portfolio_beta", 0)

        # Construct the prompt
        prompt = f"""
        You are a professional financial advisor analyzing a stock portfolio.
        Provide a comprehensive analysis of the following portfolio data:

        PORTFOLIO SUMMARY:
        - Total Value: ${total_value:.2f}
        - Portfolio Beta: {portfolio_beta:.2f}

        POSITIONS:
        {positions_text}

        Please analyze this portfolio and provide insights on:
        1. Overall risk assessment (based on beta, diversification, and position sizes)
        2. Sector concentration analysis
        3. Diversification evaluation
        4. Specific improvement recommendations

        Format your response in clear sections with headers. Be specific and actionable in your recommendations.
        """

        return prompt

    def _process_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Process and structure the raw AI response.

        Args:
            response_text: Raw text response from Gemini

        Returns:
            Dictionary with structured analysis sections
        """
        # Simple processing for MVP - future versions can implement more sophisticated parsing
        sections = {
            "risk_assessment": "",
            "sector_concentration": "",
            "diversification": "",
            "recommendations": "",
            "raw_response": response_text
        }

        # Extract sections based on headers in the response
        current_section = None

        for line in response_text.split("\n"):
            line = line.strip()

            if "risk assessment" in line.lower():
                current_section = "risk_assessment"
                continue
            elif "sector concentration" in line.lower():
                current_section = "sector_concentration"
                continue
            elif "diversification" in line.lower():
                current_section = "diversification"
                continue
            elif "recommendation" in line.lower():
                current_section = "recommendations"
                continue

            if current_section and line:
                sections[current_section] += line + "\n"

        return sections
