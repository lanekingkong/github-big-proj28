"""
Example: Context Compression for Token Savings

Demonstrates how UniSkill's context compression can save
significant token costs in AI Agent conversations.
"""

import json
from uniskill.context_engine import ContentRouter, ContextManager, CompressorFactory


def demonstrate_json_compression():
    """Show JSON compression savings."""
    print("=" * 60)
    print("JSON Compression Example")
    print("=" * 60)

    # Generate large JSON payload
    large_data = {
        "users": [
            {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "metadata": {"role": "user", "status": "active", "score": i * 10},
            }
            for i in range(100)
        ],
        "pagination": {"page": 1, "total": 1000, "per_page": 100},
    }

    json_text = json.dumps(large_data, indent=2)
    print(f"\nOriginal size: {len(json_text)} bytes")

    manager = ContextManager()
    route_result = manager._router.route(json_text)

    router = ContentRouter()
    result = router.route(json_text)

    print(f"Route result: algorithm={result.algorithm}")
    print(f"Original tokens: ~{result.original_tokens}")
    print(f"Compressed tokens: ~{result.compressed_tokens}")
    print(f"Compression ratio: {result.compression_ratio:.1%}")
    print(f"Savings: {result.savings_percent:.1f}%")


def demonstrate_code_compression():
    """Show code compression."""
    print("\n" + "=" * 60)
    print("Code Compression Example")
    print("=" * 60)

    verbose_code = """
# This is a very detailed comment block
# explaining what the function does step by step
# It processes user data and returns formatted results

def process_user_data(user_list):
    '''
    Process a list of user dictionaries and return
    formatted results with calculated metrics.
    
    Args:
        user_list: List of user dictionaries with 'name' and 'score' keys
    
    Returns:
        List of formatted result strings
    '''
    results = []
    
    # Initialize counters
    total = 0
    count = 0
    
    # Process each user
    for user in user_list:
        # Extract user data
        name = user.get('name', 'Unknown')
        score = user.get('score', 0)
        
        # Calculate metrics
        total += score
        count += 1
        
        # Format result string
        result = f"User {name}: Score {score}"
        
        # Append to results list
        results.append(result)
    
    # Calculate average
    avg = total / max(count, 1)
    
    # Add summary
    results.append(f"Average: {avg:.2f}")
    
    # Return final results
    return results
"""

    print(f"\nOriginal size: {len(verbose_code)} bytes")
    compressor = CompressorFactory().create("code")
    compressed, stats = compressor.compress(verbose_code)

    print(f"Compressed size: {len(compressed)} bytes")
    print(f"Compression ratio: {stats.compression_ratio:.1%}")
    print(f"Savings: {stats.space_saved_percent:.1f}%")

    # Show compressed version
    print(f"\nCompressed code (first 200 chars):")
    print(compressed[:200])


def demonstrate_token_budget():
    """Show token budget management."""
    print("\n" + "=" * 60)
    print("Token Budget Management Example")
    print("=" * 60)

    manager = ContextManager(max_tokens=5000)

    # Add contexts
    manager.add_context("system_prompt", "You are a helpful assistant. " * 50)
    manager.add_context("user_message_1", "Hello! " * 100)
    manager.add_context("user_message_2", "Tell me about AI. " * 200)

    stats = manager.get_stats()
    print(f"\nTotal tokens: {stats['total_tokens']}")
    print(f"Compressions performed: {stats['total_compressions']}")
    print(f"Context items: {stats['context_count']}")
    print(f"Current compression ratio: {stats['compression_ratio']:.1%}")


if __name__ == "__main__":
    demonstrate_json_compression()
    demonstrate_code_compression()
    demonstrate_token_budget()
