#!/usr/bin/env python3
"""
Robust LinkedIn Feed Scraper using Playwright
Scrapes LinkedIn feed posts with improved error handling and browser compatibility.
"""

import asyncio
from playwright.async_api import async_playwright

class RobustLinkedInScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None

    async def start_browser(self, headless=False):
        """Start browser"""
        print("🚀 Starting LinkedIn Scraper...")
        
        self.playwright = await async_playwright().start()
        
        try:
            print("🌐 Launching Microsoft Edge...")
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                channel="msedge"
            )
        except Exception:
            print("⚠️  Using Chromium instead...")
            self.browser = await self.playwright.chromium.launch(headless=headless)
        
        self.page = await self.browser.new_page()
        
        print("🔗 Opening LinkedIn login...")
        await self.page.goto('https://www.linkedin.com/login')
        
        print("\n" + "="*50)
        print("Please complete these steps:")
        print("1. Log into LinkedIn")
        print("2. Go to your feed (Home page)")
        print("3. Come back and press Enter")
        print("="*50)
        
        return True

    async def wait_for_user_and_scrape(self, num_posts=5):
        """Wait for user to be ready, then scrape"""
        input("\nPress Enter when you're on your LinkedIn feed...")
        
        # Check current page
        try:
            url = self.page.url
            print(f"📍 Current URL: {url}")
            
            if 'linkedin.com' not in url:
                print("❌ Please navigate to LinkedIn first")
                return []
            
            # Wait for page to be stable
            await asyncio.sleep(2)
            
            print("🔍 Looking for posts...")
            
            # Try to find posts with a very simple approach
            posts_data = await self.page.evaluate(f"""
                () => {{
                    const posts = [];
                    
                    // Try multiple selectors
                    const selectors = [
                        'div[data-id]',
                        '.feed-shared-update-v2',
                        'article',
                        '.occludable-update',
                        '[data-urn]'
                    ];
                    
                    for (const selector of selectors) {{
                        const elements = document.querySelectorAll(selector);
                        console.log(`Found ${{elements.length}} elements with ${{selector}}`);
                        
                        if (elements.length > 0) {{
                            for (let i = 0; i < Math.min({num_posts}, elements.length); i++) {{
                                const element = elements[i];
                                const text = element.innerText || element.textContent || '';
                                
                                if (text.length > 50) {{
                                    posts.push({{
                                        number: posts.length + 1,
                                        content: text.substring(0, 600),
                                        selector: selector
                                    }});
                                }}
                                
                                if (posts.length >= {num_posts}) break;
                            }}
                            break;
                        }}
                    }}
                    
                    return posts;
                }}
            """)
            
            return posts_data
            
        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            return []

    def display_results(self, posts):
        """Display the scraped posts"""
        if not posts:
            print("\n❌ No posts found!")
            print("This could mean:")
            print("- You're not on the LinkedIn feed page")
            print("- LinkedIn has changed their layout")
            print("- The page hasn't loaded completely")
            return
        
        print(f"\n✅ Found {len(posts)} posts!")
        print("="*60)
        
        for post in posts:
            print(f"\n📝 POST #{post['number']}")
            print("-" * 30)
            print(post['content'])
            print(f"\n[Detected using: {post['selector']}]")
            print("="*60)
    
    async def close(self):
        """Cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass

async def main():
    """Main function to run the LinkedIn scraper"""
    scraper = RobustLinkedInScraper()
    
    try:
        await scraper.start_browser()
        posts = await scraper.wait_for_user_and_scrape(num_posts=5)
        scraper.display_results(posts)
        
    except KeyboardInterrupt:
        print("\n⚠️  Stopped by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await scraper.close()
        print("\n🏁 Scraper finished!")

if __name__ == "__main__":
    asyncio.run(main())