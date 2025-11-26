#!/usr/bin/env python3
"""
Test Agent with Verbose Feedback
Shows exactly what's happening at each step
"""
import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, Timeout

# Add project to path
sys.path.insert(0, '/Users/terryroberts/Documents/code/web3_mud')

def main():
    print("🚀 Starting Agent Test")
    print("=" * 70)
    
    # Step 1: Load environment
    print("\n[1/5] Loading environment variables...")
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        sys.exit(1)
    
    print(f"✓ API key loaded (starts with: {api_key[:10]}...)")
    
    # Step 2: Initialize OpenAI client
    print("\n[2/5] Initializing OpenAI client...")
    try:
        client = OpenAI(api_key=api_key, timeout=30.0)
        print("✓ Client initialized with 30s timeout")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        sys.exit(1)
    
    # Step 3: Prepare request
    print("\n[3/5] Preparing API request...")
    messages = [
        {"role": "system", "content": "You are a name generator for a fantasy world. Generate names that fit Anglo/Celtic naming conventions."},
        {"role": "user", "content": "Generate exactly 3 character names for the Sunward Kingdoms. Just list the names, nothing else."}
    ]
    print("✓ Messages prepared")
    print(f"   Model: gpt-4o-mini")
    print(f"   Timeout: 30 seconds")
    
    # Step 4: Make API call
    print("\n[4/5] Calling OpenAI API...")
    print("   (This may take 5-15 seconds)")
    
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
            timeout=30.0
        )
        
        elapsed = time.time() - start_time
        print(f"✓ API call succeeded in {elapsed:.2f}s")
        
        # Step 5: Display result
        print("\n[5/5] Processing response...")
        result = response.choices[0].message.content
        
        print("\n" + "=" * 70)
        print("📋 RESULT:")
        print(result)
        print("="  * 70)
        
        print("\n✅ Test completed successfully!")
        return 0
        
    except Timeout as e:
        elapsed = time.time() - start_time
        print(f"\n❌ TIMEOUT after {elapsed:.2f}s")
        print(f"   Error: {str(e)}")
        return 1
        
    except APIConnectionError as e:
        elapsed = time.time() - start_time
        print(f"\n❌ CONNECTION ERROR after {elapsed:.2f}s")
        print(f"   Error: {str(e)}")
        print(f"   Hint: Check your internet connection")
        return 1
        
    except RateLimitError as e:
        elapsed = time.time() - start_time
        print(f"\n❌ RATE LIMIT ERROR after {elapsed:.2f}s")
        print(f"   Error: {str(e)}")
        print(f"   Hint: You've hit OpenAI rate limits, wait a moment")
        return 1
        
    except APIError as e:
        elapsed = time.time() - start_time
        print(f"\n❌ API ERROR after {elapsed:.2f}s")
        print(f"   Status code: {e.status_code if hasattr(e, 'status_code') else 'unknown'}")
        print(f"   Error: {str(e)}")
        return 1
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ UNEXPECTED ERROR after {elapsed:.2f}s")
        print(f"   Type: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        import traceback
        print("\n   Full traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
