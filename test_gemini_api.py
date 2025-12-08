#!/usr/bin/env python3
"""Quick test script to verify Gemini API key works"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file")
    exit(1)

print("🔑 Testing Gemini API Key...")
print(f"   Key: {api_key[:20]}...{api_key[-10:]}")
print()

# Configure Gemini
genai.configure(api_key=api_key)

# Test with gemini-2.5-flash
print("📡 Testing gemini-2.5-flash model...")
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("Say hello in one sentence")
    
    print("✅ SUCCESS! API key is working with gemini-2.5-flash!")
    print(f"📝 Response: {response.text}")
    print()
    
    # Show quota info
    print("📊 API Test Results:")
    print("   Model: gemini-2.5-flash")
    print("   Status: ✅ Active")
    print("   Quota: ✅ Available")
    
except Exception as e:
    print("❌ ERROR: API key test failed")
    print(f"   Error: {str(e)}")
    print()
    
    if "quota" in str(e).lower():
        print("💡 This looks like a quota issue:")
        print("   - Your API key might have hit the daily limit")
        print("   - Create a new API key at: https://makersuite.google.com/app/apikey")
        print("   - Make sure Gemini API is enabled in your Google Cloud project")
    elif "invalid" in str(e).lower():
        print("💡 This looks like an invalid key:")
        print("   - Double-check your GEMINI_API_KEY in .env")
        print("   - Get a new key at: https://makersuite.google.com/app/apikey")
    
    exit(1)

print()
print("🎯 Next steps:")
print("   1. If this worked, update the same key in HuggingFace Spaces")
print("   2. Go to: https://huggingface.co/spaces/Hiren158/rag-microservice/settings")
print("   3. Update GEMINI_API_KEY in Variables and secrets")
print("   4. Wait for Space to restart")
