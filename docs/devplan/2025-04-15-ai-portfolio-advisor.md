# AI Portfolio Advisor Integration

**Date:** 2025-04-15
**Author:** Dong Ming
**Status:** Draft
**Supersedes:** [2025-04-10-gemini-ai-portfolio-analysis.md](2025-04-10-gemini-ai-portfolio-analysis.md)

## Overview

This document outlines the updated design and implementation plan for integrating Google Gemini AI into the Folio portfolio dashboard application. Based on our progress and evolving requirements, we're shifting from a static portfolio analysis feature to a more interactive AI portfolio advisor that can both analyze portfolios and engage in conversations with users about their investments.

## Changes from Previous Plan

The original plan (2025-04-10) focused on a button-triggered portfolio analysis with a structured display of results. Key changes in this updated plan include:

1. **Shift to Conversational Interface**: Moving from a static analysis display to an interactive chat interface where users can ask questions about their portfolio.

2. **Expanded Scope**: The AI will function as a comprehensive portfolio advisor rather than just an analysis tool, offering advice, answering questions, and providing insights.

3. **Focused Domain Expertise**: The AI will be explicitly instructed to stay within its financial advisory role and refuse to answer questions unrelated to investments and portfolios.

4. **Updated Model**: Using the newer `gemini-2.5-pro-exp-03-25` model for improved capabilities.

5. **Simplified UI**: Using a chat button in the corner rather than an analysis button above the portfolio table.

## Current Implementation Status

We have made significant progress on the AI integration:

1. **UI Components**: Implemented a chat button and panel in the bottom right corner of the application.

2. **Basic Client**: Created the `GeminiClient` class for interacting with the Gemini API.

3. **System Prompt**: Defined a clear system prompt that establishes the AI's role as a portfolio advisor.

4. **Data Preparation**: Implemented the `prepare_portfolio_data_for_analysis` function to format portfolio data for the AI.

However, the current implementation has some gaps:

1. **Incomplete Integration**: The chat interface is not yet connected to the `GeminiClient`.

2. **Hardcoded Responses**: The current chat implementation uses hardcoded responses instead of the Gemini API.

3. **Limited Functionality**: The AI cannot yet analyze the portfolio data in real-time or respond to specific questions about it.

## Implementation Checklist

- [x] Phase 1: Basic Chat UI (Completed)
- [ ] Phase 2: Gemini API Integration
- [ ] Phase 3: Portfolio Analysis Capabilities
- [ ] Phase 4: Enhanced Conversational Features

## Feature Requirements

### Phase 2: Gemini API Integration

1. **Connect Chat Interface to Gemini API**
   - Replace hardcoded responses with actual API calls
   - Implement proper error handling and loading states
   - Add conversation history management

2. **Portfolio Data Integration**
   - Pass current portfolio data to the AI for context
   - Enable the AI to reference specific holdings and metrics
   - Format portfolio data for optimal AI understanding

3. **System Prompt Refinement**
   - Fine-tune the system prompt for the portfolio advisor role
   - Add specific instructions for handling different types of financial questions
   - Implement guardrails to keep responses within the financial domain

### Phase 3: Portfolio Analysis Capabilities

1. **Automated Initial Analysis**
   - Provide an initial portfolio assessment when chat is first opened
   - Highlight key metrics, risks, and opportunities
   - Suggest areas for the user to explore further

2. **Specific Analysis Capabilities**
   - Risk assessment (beta, concentration, diversification)
   - Sector and asset allocation analysis
   - Performance attribution
   - Tax efficiency evaluation

3. **Visualization Integration**
   - Generate descriptions of portfolio visualizations
   - Reference charts and graphs in the UI when relevant
   - Explain patterns and trends visible in the data

### Phase 4: Enhanced Conversational Features

1. **Follow-up Questions**
   - Maintain context across multiple exchanges
   - Ask clarifying questions when user intent is unclear
   - Provide increasingly detailed analysis based on conversation flow

2. **Scenario Analysis**
   - Answer "what if" questions about portfolio changes
   - Simulate adding or removing positions
   - Project potential outcomes of rebalancing decisions

3. **Personalized Recommendations**
   - Adapt advice based on stated investment goals
   - Consider risk tolerance in recommendations
   - Provide actionable, specific suggestions

## Technical Design

### 1. Chat Interface Integration

Update the `send_chat_message` function in `app.py` to use the `GeminiClient`:

```python
@app.callback(
    [
        Output("chat-messages", "children"),
        Output("chat-input", "value")
    ],
    [
        Input("chat-send", "n_clicks"),
        Input("chat-input", "n_submit")
    ],
    [
        State("chat-input", "value"),
        State("chat-messages", "children"),
        State("portfolio-groups", "data"),
        State("portfolio-summary", "data"),
        State("chat-history", "data")  # Add a store for chat history
    ],
    prevent_initial_call=True
)
async def send_chat_message(send_clicks, input_submit, message, current_messages, 
                           groups_data, summary_data, chat_history):
    """Send a message to the AI and display the response"""
    if not send_clicks and not input_submit or not message or message.strip() == "":
        raise PreventUpdate
        
    # Initialize chat history if needed
    if chat_history is None:
        chat_history = []
    
    # Get current messages or initialize
    if current_messages is None:
        current_messages = []
    
    # Add user message to display
    user_message = html.Div(message, className="user-message")
    updated_messages = current_messages + [user_message]
    
    # Add loading message
    loading_message = html.Div("Thinking...", className="ai-message loading")
    messages_with_loading = updated_messages + [loading_message]
    
    # Update chat history
    chat_history.append({"role": "user", "content": message})
    
    try:
        # Check if we have portfolio data
        if not groups_data or not summary_data:
            ai_response = "I don't see any portfolio data loaded yet. Please upload a portfolio file or load the sample portfolio first, then I can help analyze it."
        else:
            # Prepare portfolio data for analysis
            groups = [PortfolioGroup.from_dict(g) for g in groups_data]
            summary = PortfolioSummary.from_dict(summary_data)
            portfolio_data = prepare_portfolio_data_for_analysis(groups, summary)
            
            # Initialize Gemini client
            client = GeminiClient()
            
            # Get response from Gemini
            response = await client.chat(message, chat_history, portfolio_data)
            ai_response = response.get("response", "I'm sorry, I couldn't generate a response. Please try again.")
    
    except Exception as e:
        logger.error(f"Error in AI chat: {str(e)}", exc_info=True)
        ai_response = f"I encountered an error while processing your request. Please try again later."
    
    # Add AI response to chat history
    chat_history.append({"role": "assistant", "content": ai_response})
    
    # Add AI message to display
    ai_message = html.Div(ai_response, className="ai-message")
    
    # Return updated messages and clear input
    return updated_messages + [ai_message], "", chat_history
```

### 2. Enhanced GeminiClient

Update the `GeminiClient` class to support chat functionality:

```python
async def chat(self, message: str, history: List[Dict[str, str]], 
              portfolio_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a response to a user message in the context of their portfolio.
    
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
            formatted_history.append({
                "role": msg["role"],
                "parts": [msg["content"]]
            })
        
        # Add the current message
        formatted_history.append({
            "role": "user",
            "parts": [message]
        })
        
        # If we have portfolio context, add it to the first user message
        if context and formatted_history:
            for i, msg in enumerate(formatted_history):
                if msg["role"] == "user":
                    formatted_history[i]["parts"] = [context + "\n\n" + msg["parts"][0]]
                    break
        
        # Generate response
        response = await self.model.generate_content_async(formatted_history)
        
        return {
            "response": response.text,
            "complete": True
        }
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        return {
            "response": f"I encountered an error: {str(e)}",
            "complete": False,
            "error": True
        }
        
def _create_conversation_context(self, portfolio_data: Optional[Dict[str, Any]]) -> str:
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
    sorted_positions = sorted(positions, key=lambda p: abs(p.get("market_value", 0)), reverse=True)
    top_positions = sorted_positions[:10]
    
    positions_text = "\n".join([
        f"- {pos['ticker']}: {pos['position_type'].upper()}, "
        f"Value: ${pos['market_value']:.2f}, "
        f"Beta: {pos['beta']:.2f}, "
        f"Weight: {pos['weight']:.2%}"
        for pos in top_positions
    ])
    
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
```

### 3. Add Chat History Store

Add a dcc.Store component to maintain chat history:

```python
# Add to app layout
dcc.Store(id="chat-history", storage_type="session")
```

### 4. CSS Styling

Add additional CSS for chat loading state:

```css
/* Chat loading animation */
.ai-message.loading {
    position: relative;
    min-height: 24px;
}

.ai-message.loading::after {
    content: "...";
    animation: loading-dots 1.5s infinite;
}

@keyframes loading-dots {
    0%, 20% { content: "."; }
    40% { content: ".."; }
    60%, 100% { content: "..."; }
}
```

## Implementation Plan

### Phase 2: Gemini API Integration (3 days)

1. **Day 1: Chat Client Enhancement**
   - Update the `GeminiClient` class with chat functionality
   - Implement conversation context creation
   - Add chat history management

2. **Day 2: UI Integration**
   - Connect the chat interface to the Gemini API
   - Add loading states and error handling
   - Implement the chat history store

3. **Day 3: Testing and Refinement**
   - Test with various portfolio compositions
   - Refine system prompt based on response quality
   - Add handling for edge cases and error conditions

### Phase 3: Portfolio Analysis Capabilities (4 days)

1. **Day 1-2: Initial Analysis Implementation**
   - Create specialized prompts for portfolio analysis
   - Implement automatic initial assessment
   - Add detailed portfolio metrics to context

2. **Day 3-4: Specialized Analysis Features**
   - Implement sector and allocation analysis
   - Add risk assessment capabilities
   - Create performance attribution functionality

### Phase 4: Enhanced Conversational Features (5 days)

1. **Day 1-2: Conversation Flow Improvements**
   - Enhance context management across exchanges
   - Implement clarifying questions
   - Add follow-up suggestion capabilities

2. **Day 3-5: Advanced Features**
   - Implement scenario analysis functionality
   - Add personalized recommendation capabilities
   - Create visualization integration features

## Security and Privacy Considerations

1. **API Key Management**
   - Store API keys securely in environment variables
   - Never expose API keys in client-side code
   - Implement key rotation procedures

2. **Data Privacy**
   - Only send necessary portfolio data to the API
   - Do not include personally identifiable information
   - Implement data minimization principles

3. **Content Filtering**
   - Enforce strict boundaries on AI responses
   - Ensure the AI stays within its financial advisory role
   - Implement detection for potentially harmful requests

## Testing Strategy

1. **Unit Tests**
   - Test chat functionality with mock responses
   - Test portfolio data preparation
   - Test conversation context creation

2. **Integration Tests**
   - Test end-to-end chat flow with mock portfolios
   - Verify UI updates correctly with AI responses
   - Test error handling and edge cases

3. **Prompt Engineering Tests**
   - Evaluate response quality with different portfolio compositions
   - Test boundary enforcement (non-financial questions)
   - Verify advice quality and accuracy

## Conclusion

The AI Portfolio Advisor integration transforms Folio from a data visualization tool into an interactive financial assistant. By leveraging the Gemini AI model with a carefully crafted system prompt and portfolio context, we can provide users with personalized insights, analysis, and recommendations about their investments.

This updated plan reflects our progress so far and the shift toward a more conversational, advisor-like experience rather than just static analysis. The phased approach allows for incremental delivery while building toward a sophisticated AI-powered financial assistant within the Folio application.
