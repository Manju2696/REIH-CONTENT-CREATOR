"""
Cost Calculator for OpenAI API Usage
Calculates costs based on token usage and model pricing
"""

# OpenAI Pricing (per 1,000 tokens) - limited to supported models
PRICING = {
    'gpt-5': {
        'input': 0.02,
        'output': 0.06
    },
    'gpt-5.1': {
        'input': 0.02,   # Approximate placeholder pricing
        'output': 0.06
    },
    'gpt-4o': {
        'input': 0.005,
        'output': 0.015
    },
    'gpt-4o-mini': {
        'input': 0.00015,
        'output': 0.0006
    }
}

def get_model_pricing(model_name):
    """
    Get pricing for a specific model.
    Returns default gpt-4o-mini pricing if model not found.
    """
    # Normalize model name (remove any version suffixes)
    model_key = model_name.lower()
    
    # Check for exact match first
    if model_key in PRICING:
        return PRICING[model_key]
    
    # Check for partial matches
    if 'gpt-5.1' in model_key:
        return PRICING['gpt-5.1']
    elif 'gpt-5' in model_key:
        return PRICING['gpt-5']
    elif 'gpt-4o-mini' in model_key:
        return PRICING['gpt-4o-mini']
    elif 'gpt-4o' in model_key:
        return PRICING['gpt-4o']
    
    # Default to gpt-4o-mini pricing
    return PRICING['gpt-4o-mini']

def calculate_cost(input_tokens, output_tokens, model_name):
    """
    Calculate the cost for token usage.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model_name: Name of the OpenAI model used
    
    Returns:
        Dictionary with 'input_cost', 'output_cost', and 'total_cost' in USD
    """
    pricing = get_model_pricing(model_name)
    
    # Calculate costs (tokens / 1000 * price per 1K tokens)
    input_cost = (input_tokens / 1000.0) * pricing['input']
    output_cost = (output_tokens / 1000.0) * pricing['output']
    total_cost = input_cost + output_cost
    
    return {
        'input_cost': round(input_cost, 6),
        'output_cost': round(output_cost, 6),
        'total_cost': round(total_cost, 6),
        'model': model_name
    }

def format_cost(cost):
    """
    Format cost for display.
    
    Args:
        cost: Cost in USD (float)
    
    Returns:
        Formatted string (e.g., "$0.001", "$0.50", "$1.23")
    """
    if cost < 0.001:
        return f"${cost:.6f}"
    elif cost < 1:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"

