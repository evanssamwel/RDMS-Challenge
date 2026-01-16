
from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        pass
    def handle_endtag(self, tag):
        pass
    def handle_data(self, data):
        pass

try:
    with open(r'C:\Users\E.Samwel\Desktop\RDMS\web_demo\templates\studio.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = MyHTMLParser()
    parser.feed(content)
    print("HTML Parsed successfully.")
except Exception as e:
    print(f"HTML Parsing Failed: {e}")
