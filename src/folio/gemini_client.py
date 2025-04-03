"""Google Gemini AI client for portfolio analysis."""

import logging
import os
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from .ai_utils import PORTFOLIO_ADVISOR_SYSTEM_PROMPT

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
            model_name="gemini-2.5-pro-exp-03-25",
            generation_config=GenerationConfig(
                temperature=0.2,
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            ),
            # Set the system prompt to ensure the AI stays focused on portfolio advising
            system_instruction=PORTFOLIO_ADVISOR_SYSTEM_PROMPT,
        )
        logger.info(
            "Gemini client initialized successfully with portfolio advisor system prompt"
        )

    async def chat(
        self,
        message: str,
        history: list[dict[str, str]],
        portfolio_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a response to a user message in the context of their portfolio (async version).

        Args:
            message: The user's message
            history: List of previous messages in the conversation
            portfolio_data: Optional dictionary containing portfolio information

        Returns:
            Dictionary with the AI response and any additional data
        """
        try:
            # Create the conversation context with portfolio data if available
            context = self._create_conversation_context(portfolio_data)

            # Format the conversation history for the model
            formatted_history = []
            for msg in history[-10:]:  # Limit to last 10 messages for context window
                formatted_history.append(
                    {"role": msg["role"], "parts": [msg["content"]]}
                )

            # Add the current message
            formatted_history.append({"role": "user", "parts": [message]})

            # If we have portfolio context, add it to the first user message
            if context and formatted_history:
                for i, msg in enumerate(formatted_history):
                    if msg["role"] == "user":
                        formatted_history[i]["parts"] = [
                            context + "\n\n" + msg["parts"][0]
                        ]
                        break

            # Generate response
            response = await self.model.generate_content_async(formatted_history)

            return {"response": response.text, "complete": True}

        except Exception as e:
            logger.error(f"Error in chat: {e!s}")
            return {
                "response": f"I encountered an error: {e!s}",
                "complete": False,
                "error": True,
            }

    def chat_sync(
        self,
        message: str,
        history: list[dict[str, str]],
        portfolio_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a response to a user message in the context of their portfolio (synchronous version).

        This method is provided for environments where async/await cannot be used.

        Args:
            message: The user's message
            history: List of previous messages in the conversation
            portfolio_data: Optional dictionary containing portfolio information

        Returns:
            Dictionary with the AI response and any additional data
        """
        try:
            # Log the start of the process
            logger.info(
                f"Starting chat_sync with message: '{message[:50]}...' and {len(history)} history items"
            )

            # Create the conversation context with portfolio data if available
            context = self._create_conversation_context(portfolio_data)
            logger.info(f"Created conversation context: {len(context)} characters")

            # Prepare the user message with context if available
            user_message = message
            if context:
                user_message = context + "\n\n" + message
                logger.info("Added portfolio context to user message")

            # Use the Gemini SDK's built-in chat functionality
            logger.info("Using Gemini SDK chat functionality")

            # Properly format history for the Gemini API
            formatted_history = []

            # Add previous messages to the history in the correct format
            if history:
                logger.info(
                    f"Formatting {len(history)} previous messages for chat history"
                )
                for msg in history[
                    -10:
                ]:  # Limit to last 10 messages for context window
                    role = "user" if msg["role"] == "user" else "model"
                    formatted_history.append(
                        {"role": role, "parts": [{"text": msg["content"]}]}
                    )

            # Create a chat session with history
            logger.info("Creating new chat session with history")
            chat = self.model.start_chat(history=formatted_history)

            # Send the current message
            logger.info("Sending message to chat session")
            response = chat.send_message(user_message)
            logger.info(
                f"Received response from Gemini API: {len(response.text)} characters"
            )

            return {"response": response.text, "complete": True}

        except Exception as e:
            logger.error(f"Error in chat_sync: {e!s}", exc_info=True)
            return {
                "response": f"I encountered an error: {e!s}",
                "complete": False,
                "error": True,
            }

    async def analyze_portfolio(self, portfolio_data: dict[str, Any]) -> dict[str, Any]:
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
            logger.error(f"Error during portfolio analysis: {e!s}")
            return {
                "error": True,
                "message": f"Analysis failed: {e!s}",
            }

    def _create_analysis_prompt(self, portfolio_data: dict[str, Any]) -> str:
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
        positions_text = "\n".join(
            [
                f"- {pos['ticker']}: {pos['position_type'].upper()}, "
                f"Value: ${pos['market_value']:.2f}, "
                f"Beta: {pos['beta']:.2f}, "
                f"Weight: {pos['weight']:.2%}"
                for pos in positions
            ]
        )

        # Format summary data
        total_value = summary.get("total_value_net", 0)
        portfolio_beta = summary.get("portfolio_beta", 0)

        # Construct the prompt
        prompt = f"""
        You are a professional financial advisor analyzing a stock portfolio.
        Remember that you should ONLY answer questions related to finance, investments, and the client's portfolio.

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

        If the user asks about topics unrelated to finance or investments, politely redirect them back to discussing their portfolio.
        """

        return prompt

    def _create_conversation_context(
        self, portfolio_data: dict[str, Any] | None
    ) -> str:
        """
        Create a context string with portfolio information for the AI.

        Args:
            portfolio_data: Dictionary containing portfolio information

        Returns:
            Formatted context string
        """
        if not portfolio_data:
            return ""

        # Extract key portfolio metrics
        positions = portfolio_data.get("positions", [])
        summary = portfolio_data.get("summary", {})

        # Format positions data (limit to top 10 by value for context size)
        sorted_positions = sorted(
            positions, key=lambda p: abs(p.get("market_value", 0)), reverse=True
        )
        top_positions = sorted_positions[:10]

        positions_text = "\n".join(
            [
                f"- {pos['ticker']}: {pos['position_type'].upper()}, "
                f"Value: ${pos['market_value']:.2f}, "
                f"Beta: {pos['beta']:.2f}, "
                f"Weight: {pos['weight']:.2%}"
                for pos in top_positions
            ]
        )

        # Format summary data
        total_value = summary.get("total_value_net", 0)
        portfolio_beta = summary.get("portfolio_beta", 0)

        # Construct the context
        context = f"""
        PORTFOLIO CONTEXT:

        Summary:
        - Total Value: ${total_value:.2f}
        - Portfolio Beta: {portfolio_beta:.2f}
        - Number of Positions: {len(positions)}

        Top Positions:
        {positions_text}

        Use this information to provide relevant advice and analysis.
        """

        return context

    def _process_analysis_response(self, response_text: str) -> dict[str, Any]:
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
            "raw_response": response_text,
        }

        # Extract sections based on headers in the response
        current_section = None

        for line_text in response_text.split("\n"):
            line = line_text.strip()

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
