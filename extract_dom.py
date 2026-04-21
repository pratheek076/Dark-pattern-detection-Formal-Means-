#!/usr/bin/env python3
"""
Intelligently extracts cookie banners by analyzing CSS Render Layers, 
Accessibility Roles, and piercing Iframes.
"""

from playwright.sync_api import sync_playwright

# The JavaScript payload that acts as our "intelligent layer scanner"
SCANNER_JS = """() => {
    const keywords = ['cookie', 'consent', 'privacy', 'gdpr'];
    const candidates = document.querySelectorAll('div, section, dialog, aside');
    
    for (let el of candidates) {
        // 1. Accessibility Tree Check
        const isAOMDialog = el.tagName === 'DIALOG' || 
                            el.getAttribute('role') === 'dialog' || 
                            el.getAttribute('role') === 'alertdialog';
        
         console.log("Checking element:", el.tagName, "Role:", el.getAttribute('role'), "IsDialog:", isAOMDialog);                 
        // 2. Render Tree Check (Is it a visual layer/overlay?)
        const style = window.getComputedStyle(el);
        console.log("  Position:", style.position, "Display:", style.display, "Size:", el.offsetWidth + "x" + el.offsetHeight);
        
        const isRenderLayer = ['fixed', 'sticky', 'absolute'].includes(style.position);

        // If it's neither a dialog nor a floating layer, skip it
        if (!isAOMDialog && !isRenderLayer) continue;
        
        // 3. Visibility Check (Don't extract hidden layers)
        if (el.offsetWidth === 0 || el.offsetHeight === 0 || style.display === 'none') continue;
        
        // 4. Semantic Check (Does it talk about cookies?)
        const text = el.innerText.toLowerCase();
        if (!keywords.some(kw => text.includes(kw))) continue;
        
        // 5. Actionable Check (Does it have buttons?)
        const buttons = el.querySelectorAll('button, a[href], [role="button"]');
        if (buttons.length === 0) continue;
        
        // Found it! Return the clean HTML layer.
        return el.outerHTML; 
    }
    return null;
}"""

def extract_cookie_layer(url: str):
    banner_html = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Run silently
        page = browser.new_page()
        
        print(f"Scanning: {url}")
        try:
            # Wait for all third-party scripts (like TrustArc/OneTrust) to load
            page.goto(url, timeout=350000)
            page.wait_for_timeout(5000) # Buffer for slide-in CSS animations
            
            # Step 1: Scan the main document tree
            banner_html = page.evaluate(SCANNER_JS)
            
            # Step 2: Pierce Iframes (The Iframe Trap)
            # If we didn't find it in the main DOM, check every iframe on the page
            if not banner_html:
                print("Not found in main DOM. Scanning iframes...")
                for frame in page.frames:
                    try:
                        # Inject the same scanner into the iframe's isolated document
                        result = frame.evaluate(SCANNER_JS)
                        if result:
                            banner_html = result
                            break
                    except Exception:
                        pass # Ignore cross-origin frame access errors if they block JS
            
        except Exception as e:
            print(f"Failed to load page: {e}")
        finally:
            browser.close()

    # The Verdict
    if banner_html:
        print("\n✅ BANNER LAYER EXTRACTED SUCESSFULLY!\n")
        print("--- BANNER HTML SNIPPET ---")
        print(banner_html[:500] + "...\n") # Print first 500 chars to verify
        return banner_html
    else:
        print("\n❌ No cookie banner layer detected.")
        return None

if __name__ == "__main__":
    # Test it on a site you know has a banner
    extract_cookie_layer("https://travisonline.com/")