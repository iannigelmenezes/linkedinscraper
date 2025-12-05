#!/usr/bin/env python3
"""
LinkedIn Feed Scraper using Playwright
Scrapes the first 5 posts from LinkedIn feed and displays them in the terminal.
"""

import asyncio
import sys
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import time

class LinkedInScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def start_browser(self, headless=False):
        """Initialize the browser and create a new page"""
        self.playwright = await async_playwright().start()
        
        try:
            # Try to launch Microsoft Edge browser first
            print("🌐 Attempting to launch Microsoft Edge...")
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                channel="msedge",  # Use Microsoft Edge
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows'
                ]
            )
            print("✅ Microsoft Edge launched successfully!")
        except Exception as e:
            print(f"⚠️  Failed to launch Edge: {str(e)}")
            print("🔄 Falling back to Chromium...")
            # Fallback to regular Chromium
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
        
        # Create a new context with realistic Microsoft Edge user agent
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Create a new page
        self.page = await self.context.new_page()
        
        # Set additional headers
        await self.page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    async def login_to_linkedin(self):
        """Navigate to LinkedIn and handle login process"""
        try:
            print("🔗 Navigating to LinkedIn...")
            await self.page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
            
            # Wait a bit for page to fully load
            await asyncio.sleep(3)
            
            print("📝 Please log in manually in the browser window that opened.")
            print("   - Enter your LinkedIn credentials")
            print("   - Complete any 2FA if required")
            print("   - After successful login, you should see your LinkedIn feed")
            print("   - Press Enter in this terminal when you see your LinkedIn homepage/feed...")
            
            # Wait for user input
            input()
            
            # Get current URL and check
            current_url = self.page.url
            print(f"📍 Current URL: {current_url}")
            
            # Check if we're logged into LinkedIn
            if 'linkedin.com' not in current_url:
                print("⚠️  Please make sure you're on a LinkedIn page.")
                return False
            
            # Check if we're already on the feed or homepage
            if any(path in current_url for path in ['/feed/', '/in/', '/mynetwork', '/messaging']):
                print("✅ Great! You're logged into LinkedIn.")
                
                # If not on feed, navigate there
                if '/feed/' not in current_url:
                    print("🔄 Navigating to your LinkedIn feed...")
                    try:
                        # Use a more gentle navigation approach
                        await self.page.evaluate('window.location.href = "https://www.linkedin.com/feed/"')
                        await asyncio.sleep(5)  # Give it time to load
                        
                        # Wait for feed elements to appear
                        await self.page.wait_for_selector('main[aria-label*="Main content"], .feed-container-theme', timeout=15000)
                        
                    except Exception as nav_error:
                        print(f"⚠️  Navigation issue: {str(nav_error)}")
                        print("Please manually click on 'Home' or navigate to your feed.")
                        input("Press Enter when you're on your feed...")
                
                return True
            else:
                print("⚠️  Please complete the login process and try again.")
                return False
            
        except Exception as e:
            print(f"❌ Error during login process: {str(e)}")
            return False
    
    async def scrape_feed_posts(self, num_posts=5):
        """Scrape the specified number of posts from LinkedIn feed"""
        posts = []
        
        try:
            print(f"🔍 Scraping the first {num_posts} posts from your LinkedIn feed...")
            
            # Wait for feed to load with multiple possible selectors
            try:
                await self.page.wait_for_selector('div[data-id], .feed-shared-update-v2, .occludable-update', timeout=15000)
                print("✅ Feed loaded successfully!")
            except Exception as e:
                print(f"⚠️  Feed loading issue: {str(e)}")
                print("Trying alternative approach...")
                await asyncio.sleep(3)
            
            # Scroll to load more posts if needed
            print("📜 Scrolling to load more posts...")
            for i in range(3):
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)
                print(f"   Scroll {i+1}/3 completed")
            
            # Get all post containers with multiple selectors
            selectors_to_try = [
                'div[data-id]',
                '.feed-shared-update-v2',
                '.occludable-update',
                'article',
                '[data-urn]'
            ]
            
            post_elements = []
            for selector in selectors_to_try:
                post_elements = await self.page.query_selector_all(selector)
                if post_elements:
                    print(f"✅ Found {len(post_elements)} elements using selector: {selector}")
                    break
            
            if not post_elements:
                print("❌ Could not find any post elements. The page structure may have changed.")
                return []
            
            print(f"📊 Processing {min(len(post_elements), num_posts)} posts...")
            
            for i, post_element in enumerate(post_elements[:num_posts]):
                try:
                    post_data = await self.extract_post_data(post_element, i + 1)
                    if post_data:
                        posts.append(post_data)
                        print(f"✅ Extracted post {i + 1}")
                    else:
                        print(f"⚠️  Skipped post {i + 1} (no content found)")
                
                except Exception as e:
                    print(f"⚠️  Error extracting post {i + 1}: {str(e)}")
                    continue
            
            return posts
            
        except Exception as e:
            print(f"❌ Error scraping feed: {str(e)}")
            return []
    
    async def extract_post_data(self, post_element, post_number):
        """Extract data from a single post element"""
        post_data = {
            'post_number': post_number,
            'author': 'Unknown',
            'content': '',
            'engagement': {},
            'timestamp': 'Unknown'
        }
        
        try:
            # Extract author name
            author_element = await post_element.query_selector('span[aria-hidden="true"]')
            if author_element:
                author_text = await author_element.inner_text()
                post_data['author'] = author_text.strip()
            
            # Extract post content
            content_selectors = [
                'div[data-id] span[dir="ltr"]',
                '.feed-shared-text',
                '.feed-shared-inline-show-more-text',
                'span[dir="ltr"]'
            ]
            
            for selector in content_selectors:
                content_elements = await post_element.query_selector_all(selector)
                if content_elements:
                    content_parts = []
                    for element in content_elements:
                        text = await element.inner_text()
                        if text and text.strip() and len(text.strip()) > 10:
                            content_parts.append(text.strip())
                    
                    if content_parts:
                        post_data['content'] = '\n'.join(content_parts[:3])  # Limit to first 3 parts
                        break
            
            # Extract engagement metrics (likes, comments, shares)
            try:
                reaction_elements = await post_element.query_selector_all('button[aria-label*="reaction"], span[aria-hidden="true"]')
                for element in reaction_elements:
                    text = await element.inner_text()
                    if text and any(keyword in text.lower() for keyword in ['like', 'comment', 'share', 'react']):
                        aria_label = await element.get_attribute('aria-label')
                        if aria_label:
                            post_data['engagement']['reactions'] = aria_label
            except:
                pass
            
            # Extract timestamp
            try:
                time_element = await post_element.query_selector('a[data-tracking-will-navigate] span[aria-hidden="true"]')
                if time_element:
                    timestamp = await time_element.inner_text()
                    post_data['timestamp'] = timestamp.strip()
            except:
                pass
            
            # Return post data if we have meaningful content
            if post_data['content'] or post_data['author'] != 'Unknown':
                return post_data
            
            return None
            
        except Exception as e:
            print(f"Error extracting post data: {str(e)}")
            return None
    
    def format_post_output(self, post_data):
        """Format post data for terminal display"""
        separator = "=" * 80
        
        output = f"""
{separator}
📝 POST #{post_data['post_number']}
{separator}
👤 Author: {post_data['author']}
🕒 Time: {post_data['timestamp']}

📄 Content:
{post_data['content'][:500]}{'...' if len(post_data['content']) > 500 else ''}

💬 Engagement: {post_data['engagement'].get('reactions', 'No engagement data')}
{separator}
"""
        return output
    
    async def close(self):
        """Close the browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"⚠️  Cleanup warning: {str(e)}")

async def main():
    """Main function to run the LinkedIn scraper"""
    scraper = LinkedInScraper()
    
    try:
        print("🚀 Starting LinkedIn Feed Scraper...")
        print("🌐 Using Microsoft Edge browser...")
        print("=" * 50)
        
        # Start browser (set headless=True to run without GUI)
        await scraper.start_browser(headless=False)
        
        # Login to LinkedIn
        login_success = await scraper.login_to_linkedin()
        if not login_success:
            print("❌ Failed to login to LinkedIn. Exiting...")
            return
        
        # Scrape posts
        posts = await scraper.scrape_feed_posts(num_posts=5)
        
        if not posts:
            print("❌ No posts were scraped. Please check your LinkedIn feed access.")
            return
        
        # Display results
        print(f"\n🎉 Successfully scraped {len(posts)} posts!")
        print("=" * 50)
        
        for post in posts:
            print(scraper.format_post_output(post))
        
        print("✅ Scraping completed successfully!")
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        
    finally:
        await scraper.close()

if __name__ == "__main__":
    # Check if we're running in an async environment
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user.")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")