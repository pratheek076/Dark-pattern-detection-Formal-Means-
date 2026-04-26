from bs4 import BeautifulSoup

with open("extracted_cookie_banner.html", "r", encoding="utf-8") as f:
    html_snippet = f.read()

soup = BeautifulSoup(html_snippet, "html.parser")

with open("facts.dl", "w", encoding="utf-8") as file:
    for node_id, element in enumerate(soup.find_all(['div', 'button'])):
        tag = element.name
        file.write(f'element({node_id}, "{tag}").\n')
        
        if tag == 'button':
            text = element.get_text(strip=True).lower()
            file.write(f'button_text({node_id}, "{text}").\n')