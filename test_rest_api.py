#!/usr/bin/env python3
"""
Playwright REST API Test Script
Tests the REST endpoints of the techblog CMS application
"""

import asyncio
import json
import sys
from playwright.async_api import async_playwright
import requests

# Configuration
BASE_URL = "http://localhost"
API_BASE_URL = f"{BASE_URL}/api"

async def test_rest_endpoints():
    """Test REST API endpoints using Playwright and requests"""

    print("🚀 Starting REST API Tests...")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"📍 API Base URL: {API_BASE_URL}")
    print("-" * 50)

    # Test 1: Health Check Endpoint
    print("\n1️⃣ Testing Health Check Endpoint")
    print("   Endpoint: /api/health/")
    try:
        response = requests.get(f"{API_BASE_URL}/health/")
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            if data.get("status") == "ok":
                print("   ✅ Health check passed!")
            else:
                print("   ❌ Health check failed - unexpected response")
        else:
            print(f"   ❌ Health check failed - status code {response.status_code}")
            print(f"   Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health check failed - connection error: {e}")
    except json.JSONDecodeError as e:
        print(f"   ❌ Health check failed - invalid JSON response: {e}")

    # Test 2: Home Page
    print("\n2️⃣ Testing Home Page")
    print("   Endpoint: /")
    try:
        response = requests.get(BASE_URL)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ Home page accessible!")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   Content Length: {len(response.text)} characters")
        else:
            print(f"   ❌ Home page failed - status code {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Home page failed - connection error: {e}")

    # Test 3: Admin Page
    print("\n3️⃣ Testing Admin Page")
    print("   Endpoint: /admin/")
    try:
        response = requests.get(f"{BASE_URL}/admin/")
        print(f"   Status Code: {response.status_code}")

        if response.status_code in [200, 302]:  # 302 is redirect to login
            print("   ✅ Admin page accessible!")
            if response.status_code == 302:
                print("   ℹ️  Redirected to login page (expected)")
        else:
            print(f"   ❌ Admin page failed - status code {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Admin page failed - connection error: {e}")

    # Test 4: Using Playwright for browser-based testing
    print("\n4️⃣ Testing with Playwright Browser")
    async with async_playwright() as p:
        try:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Test home page
            print("   🌐 Navigating to home page...")
            await page.goto(BASE_URL)
            title = await page.title()
            print(f"   Page Title: {title}")

            # Check if page loaded successfully
            content = await page.text_content('body')
            if len(content) > 0:
                print("   ✅ Page content loaded successfully!")
            else:
                print("   ❌ Page content is empty")

            # Test API endpoint via browser
            print("   🌐 Testing API endpoint via browser...")
            await page.goto(f"{API_BASE_URL}/health/")
            api_content = await page.text_content('body')
            print(f"   API Response: {api_content}")

            # Check for JSON response
            if '"status": "ok"' in api_content:
                print("   ✅ API endpoint working via browser!")
            else:
                print("   ❌ API endpoint not working properly via browser")

            await browser.close()

        except Exception as e:
            print(f"   ❌ Playwright test failed: {e}")

    print("\n" + "=" * 50)
    print("🎉 REST API Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_rest_endpoints())
