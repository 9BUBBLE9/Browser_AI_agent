from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="user_data",
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://eda.yandex.ru")
        context.close()

if __name__ == "__main__":
    main()
