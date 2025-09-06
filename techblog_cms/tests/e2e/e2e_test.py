from playwright.sync_api import sync_playwright

def test_login_dashboard_article():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # ログイン
        page.goto("http://localhost:8000/login/")
        page.wait_for_load_state('networkidle')
        page.screenshot(path="/app/logs/login_page.png")
        
        # ページが完全にロードされるまで待機
        page.wait_for_timeout(2000)
        
        # ページの内容を確認
        title = page.title()
        print(f"Page title: {title}")
        content = page.content()
        print(f"Page has login form: {'ログイン' in content}")
        
        # input要素が存在するか確認
        inputs = page.query_selector_all("input")
        print(f"Found {len(inputs)} input elements")
        for i, inp in enumerate(inputs):
            name = inp.get_attribute("name")
            type_attr = inp.get_attribute("type")
            print(f"Input {i}: name={name}, type={type_attr}")
        
        # ユーザー名フィールドが表示されるまで待機
        page.wait_for_selector("input[name=username]", timeout=10000)
        page.fill("input[name=username]", "admin")
        page.fill("input[name=password]", "admin123")
        page.screenshot(path="/app/logs/filled_form.png")
        page.click("button[type=submit]")
        page.screenshot(path="/app/logs/after_submit.png")
        # 少し待機してページがロードされるのを待つ
        page.wait_for_timeout(2000)
        current_url = page.url
        print(f"Current URL after login: {current_url}")
        page.screenshot(path="/app/logs/after_login.png")
        
        # ダッシュボードにいるか確認、もしそうでなければ移動
        if "dashboard" not in current_url:
            page.goto("http://localhost:8000/dashboard/")
            page.wait_for_load_state('networkidle')
        page.screenshot(path="/app/logs/dashboard.png")
        # 記事投稿ページに移動
        page.click("a[href*='/dashboard/articles/new']")
        page.wait_for_timeout(2000)
        current_url = page.url
        print(f"Current URL after clicking new article: {current_url}")
        page.screenshot(path="/app/logs/article_new.png")
        
        if "articles/new" not in current_url:
            page.goto("http://localhost:8000/dashboard/articles/new/")
            page.wait_for_load_state('networkidle')
        # 記事作成ページがロードされたことを確認
        page.wait_for_selector("input[name=title]", timeout=5000)
        page.screenshot(path="/app/logs/article_form.png")
        # 記事作成
        page.fill("input[name=title]", "Test Article")
        page.fill("textarea[name=content]", "Test content")
        page.click("button[type=submit]")
        # 成功確認
        page.wait_for_url("**/dashboard")
        assert "Test Article" in page.content()
        browser.close()
