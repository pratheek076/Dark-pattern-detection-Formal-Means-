
from playwright.sync_api import sync_playwright


SCANNER_JS = """() => {
    const keywords = ['cookie', 'consent', 'privacy', 'gdpr'];
    const candidates = document.querySelectorAll('div, section, dialog');
    console.log(`Found ${candidates.length} candidates total.`);

    for (let el of candidates) {
        const label = `<${el.tagName.toLowerCase()} id="${el.id}" class="${el.className}">`;

        // 1. Accessibility Tree Check
        const isAOMDialog = el.tagName === 'DIALOG' || 
                            el.getAttribute('role') === 'dialog' || 
                            el.getAttribute('role') === 'alertdialog';

        // 2. Render Tree Check
        const style = window.getComputedStyle(el);
        const isRenderLayer = ['fixed', 'sticky', 'absolute'].includes(style.position);

       
        if (!isAOMDialog && !isRenderLayer) {
            console.log(`[SKIP:LAYER]  ${label} → position:${style.position}, role:${el.getAttribute('role')}`);
            continue;
        }
        console.log(`[PASS:LAYER]  ${label} → isDialog:${isAOMDialog}, position:${style.position}`);

       
        const isVisible = el.offsetWidth > 0 && el.offsetHeight > 0 && style.display !== 'none';
        if (!isVisible) {
            console.log(`[SKIP:VISIBLE] ${label} → size:${el.offsetWidth}x${el.offsetHeight}, display:${style.display}`);
            continue;
        }
        console.log(`[PASS:VISIBLE] ${label} → size:${el.offsetWidth}x${el.offsetHeight}`);

        
        const text = el.innerText.toLowerCase();
        const matchedKeyword = keywords.find(kw => text.includes(kw));
        if (!matchedKeyword) {
            console.log(`[SKIP:KEYWORD] ${label} → none of [${keywords}] found in text snippet: "${text.slice(0, 60)}..."`);
            continue;
        }
        console.log(`[PASS:KEYWORD] ${label} → matched keyword: "${matchedKeyword}"`);

        
        const buttons = el.querySelectorAll('button, a[href], [role="button"]');
        if (buttons.length === 0) {
            console.log(`[SKIP:BUTTONS] ${label} → no buttons found`);
            continue;
        }
        const buttonLabels = [...buttons].map(b => b.innerText.trim() || b.getAttribute('aria-label')).join(' | ');
        console.log(`[PASS:BUTTONS] ${label} → ${buttons.length} buttons found: [${buttonLabels}]`);

        console.log(`[FOUND] Cookie banner identified: ${label}`);
        return el.outerHTML;
    }

    console.log("No cookie banner found after scanning all candidates.");
    return null;
}"""

def extract_cookie_layer(url: str):
    banner_html = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print(f"Scanning: {url}")
        try:
           
            page.goto(url, timeout=30000)
            page.wait_for_timeout(4000) 
            
        
            banner_html = page.evaluate(SCANNER_JS)
            
            if not banner_html:
                print("Not found in main DOM. Scanning iframes...")
                for frame in page.frames:
                    try:
                       
                        result = frame.evaluate(SCANNER_JS)
                        if result:
                            banner_html = result
                            break
                    except Exception:
                        pass 
            
        except Exception as e:
            print(f"Failed to load page: {e}")
        finally:
            browser.close()

    if banner_html:
        print("\n Cookie banner layer extraction successful!\n")
        print("--- Cookie banner HTML snippet ---")
        print(banner_html[:500] + "...\n")
        return banner_html
    else:
        print("\n No cookie banner layer detected.")
        return None

if __name__ == "__main__":
    result = extract_cookie_layer("https://www.dishoom.com/")
    if result:
        output_file = "extracted_cookie_banner.html"
        with open(output_file, "w", encoding="utf-8") as f:
             f.write(f"<!DOCTYPE html><html><body>\n{result}\n</body></html>")
        print(f"Extracted banner saved to: {output_file}")