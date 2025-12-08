#!/usr/bin/env python3
"""List all available Gemini models for your API key"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

print("🔍 Listing all available models...")
print(f"🔑 API Key: {api_key[:20]}...{api_key[-10:]}")
print()

genai.configure(api_key=api_key)

try:
    models = genai.list_models()
    
    # Filter models that support generateContent
    generate_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
    
    print(f"✅ Found {len(generate_models)} models that support generateContent:\n")
    
    for model in generate_models:
        print(f"📝 {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description[:80]}...")
        print()
    
    print("\n💡 Try using one of these models in your app!")
    
except Exception as e:
    print(f"❌ Error listing models: {e}")
