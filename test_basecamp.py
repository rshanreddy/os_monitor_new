#!/usr/bin/env python3
import os
import logging
from core_monitor import post_to_basecamp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_md():
    """Create a simple test markdown file"""
    content = """# Test Post from OS Monitor

This is a test post to verify Basecamp integration.

## Test Details
- Time: 2025-04-17
- Environment: Test
- Status: Testing

If you can see this message, the Basecamp integration is working correctly!
"""
    
    test_file = "test_post.md"
    with open(test_file, "w") as f:
        f.write(content)
    return test_file

def main():
    # Set environment to test
    os.environ['ENV'] = 'test'
    
    # Create test markdown file
    test_file = create_test_md()
    
    try:
        # Attempt to post to Basecamp
        post_to_basecamp(test_file, subject="Test Post - Please Ignore")
    finally:
        # Clean up the test file
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    main()
