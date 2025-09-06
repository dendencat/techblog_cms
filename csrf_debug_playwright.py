#!/usr/bin/env python3
"""
CSRF Debug Script using Playwright
This script automates browser interaction to debug CSRF issues in the article editor.
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_csrf():
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to the site
            print("Navigating to the site...")
            await page.goto("https://blog.iohub.link")

            # Wait for page to load
            await page.wait_for_load_state('networkidle')

            # Take screenshot of initial page
            await page.screenshot(path="/var/lib/sdc/work/container/docker/techblog_cms/csrf_debug_initial.png")

            # Look for login link/button
            print("Looking for login...")
            login_selectors = [
                'a[href*="login"]',
                'button:has-text("Login")',
                'a:has-text("Login")',
                '[data-testid*="login"]'
            ]

            login_element = None
            for selector in login_selectors:
                try:
                    login_element = await page.query_selector(selector)
                    if login_element:
                        print(f"Found login element with selector: {selector}")
                        break
                except:
                    continue

            if login_element:
                await login_element.click()
                await page.wait_for_load_state('networkidle')
                await page.screenshot(path="/var/lib/sdc/work/container/docker/techblog_cms/csrf_debug_login_page.png")

                # Fill login form (you may need to adjust selectors based on actual form)
                try:
                    await page.fill('input[name="username"]', 'your_username')
                    await page.fill('input[name="password"]', 'your_password')
                    await page.click('input[type="submit"]')
                    await page.wait_for_load_state('networkidle')
                    await page.screenshot(path="/var/lib/sdc/work/container/docker/techblog_cms/csrf_debug_after_login.png")
                    print("Login successful")
                except Exception as e:
                    print(f"Login failed: {e}")
            else:
                print("Login element not found, assuming already logged in or different auth method")

            # Navigate to article editor
            print("Navigating to article editor...")
            editor_urls = [
                "/admin/techblog_cms/article/add/",
                "/article/new",
                "/editor",
                "/admin/"
            ]

            for url in editor_urls:
                try:
                    await page.goto(f"https://blog.iohub.link{url}")
                    await page.wait_for_load_state('networkidle')
                    if "article" in page.url or "editor" in page.url or "admin" in page.url:
                        print(f"Successfully navigated to: {page.url}")
                        break
                except:
                    continue

            await page.screenshot(path="/var/lib/sdc/work/container/docker/techblog_cms/csrf_debug_editor.png")

            # Inspect the page for CSRF token
            print("Inspecting page for CSRF token...")

            # Look for CSRF token in form
            csrf_selectors = [
                'input[name="csrfmiddlewaretoken"]',
                'input[name="csrf_token"]',
                'input[name="_csrf"]',
                'meta[name="csrf-token"]'
            ]

            csrf_token = None
            for selector in csrf_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        csrf_token = await element.get_attribute('value')
                        print(f"Found CSRF token with selector: {selector}")
                        print(f"CSRF Token: {csrf_token}")
                        break
                except:
                    continue

            if not csrf_token:
                print("CSRF token not found in common selectors")
                # Try to find any hidden input that might be CSRF
                hidden_inputs = await page.query_selector_all('input[type="hidden"]')
                for inp in hidden_inputs:
                    name = await inp.get_attribute('name')
                    value = await inp.get_attribute('value')
                    print(f"Hidden input: {name} = {value}")

            # Look for form with method POST
            forms = await page.query_selector_all('form[method="post"]')
            print(f"Found {len(forms)} POST forms")

            for i, form in enumerate(forms):
                action = await form.get_attribute('action') or ''
                print(f"Form {i+1}: action={action}")

                # Get form HTML
                form_html = await form.inner_html()
                print(f"Form {i+1} HTML:\n{form_html}\n")

            # Try to submit a form if found
            if forms:
                print("Attempting to submit the first form...")
                try:
                    # Fill some basic fields if they exist
                    try:
                        await page.fill('input[name="title"]', 'Test Article')
                    except:
                        pass
                    try:
                        await page.fill('textarea[name="content"]', 'Test content')
                    except:
                        pass

                    # Submit the form
                    await page.click('input[type="submit"]', timeout=5000)
                    await page.wait_for_load_state('networkidle')
                    await page.screenshot(path="/var/lib/sdc/work/container/docker/techblog_cms/csrf_debug_after_submit.png")
                    print("Form submitted successfully")

                except Exception as e:
                    print(f"Form submission failed: {e}")
                    # Check for error messages
                    error_selectors = [
                        '.error',
                        '.alert-danger',
                        '.errorlist',
                        '[class*="error"]'
                    ]
                    for selector in error_selectors:
                        try:
                            error_element = await page.query_selector(selector)
                            if error_element:
                                error_text = await error_element.inner_text()
                                print(f"Error message found: {error_text}")
                        except:
                            continue

            # Capture network requests
            print("Capturing network requests...")
            requests = []
            responses = []

            def on_request(request):
                requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers)
                })

            def on_response(response):
                responses.append({
                    'url': response.url,
                    'status': response.status,
                    'headers': dict(response.headers)
                })

            page.on('request', on_request)
            page.on('response', on_response)

            # Reload the page to capture requests
            await page.reload()
            await page.wait_for_load_state('networkidle')

            print(f"Captured {len(requests)} requests and {len(responses)} responses")

            # Look for POST requests that might be the form submission
            post_requests = [r for r in requests if r['method'] == 'POST']
            for req in post_requests:
                print(f"POST Request: {req['url']}")
                if 'csrf' in str(req['headers']).lower():
                    print("CSRF related headers found in request")

            # Save network data
            with open('/var/lib/sdc/work/container/docker/techblog_cms/csrf_debug_network.txt', 'w') as f:
                f.write("REQUESTS:\n")
                for req in requests:
                    f.write(f"{req}\n")
                f.write("\nRESPONSES:\n")
                for resp in responses:
                    f.write(f"{resp}\n")

        except Exception as e:
            print(f"Error during debugging: {e}")
            await page.screenshot(path="/var/lib/sdc/work/container/docker/techblog_cms/csrf_debug_error.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_csrf())
