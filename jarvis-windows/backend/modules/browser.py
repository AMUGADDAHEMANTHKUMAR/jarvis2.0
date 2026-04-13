from playwright.sync_api import sync_playwright
import webbrowser

def browse(url: str) -> str:
    try:
        webbrowser.open(url)
        return f"Opened {url} in your default browser"
    except Exception as e:
        return f"Failed to open {url}"

def search_web(query: str) -> str:
    try:
        url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}&ia=web"
        webbrowser.open(url)
        return f"Searched for '{query}' on DuckDuckGo"
    except Exception as e:
        return f"Failed to search for '{query}'"