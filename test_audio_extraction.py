"""測試從 HTML 中提取音訊連結"""

from pathlib import Path
from html.parser import HTMLParser
import html


class AudioLinkExtractor(HTMLParser):
    """從 HTML 中提取音訊下載連結的解析器"""
    
    def __init__(self):
        super().__init__()
        self.audio_link = None
        self.found = False
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a' and not self.found:
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value and 'mime=audio%2F' in attr_value:
                    # 找到音訊連結，解碼 HTML 實體
                    self.audio_link = html.unescape(attr_value)
                    self.found = True
                    print(f"✓ 找到音訊連結!")
                    print(f"原始: {attr_value[:100]}...")
                    print(f"解碼後: {self.audio_link[:100]}...")
                    break


def test_extraction():
    # 讀取最新的 HTML 檔案
    html_dir = Path("html_responses")
    html_files = list(html_dir.glob("*.html"))
    
    if not html_files:
        print("❌ 沒有找到 HTML 檔案")
        return
    
    # 取得最新的檔案
    latest_file = max(html_files, key=lambda p: p.stat().st_mtime)
    print(f"正在測試檔案: {latest_file}\n")
    
    # 讀取 HTML 內容
    with open(latest_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"HTML 檔案大小: {len(html_content)} 字元\n")
    
    # 測試提取
    parser = AudioLinkExtractor()
    parser.feed(html_content)
    
    if parser.audio_link:
        print(f"\n✅ 成功提取音訊連結!")
        print(f"完整連結長度: {len(parser.audio_link)} 字元")
        print(f"\n前 200 字元:")
        print(parser.audio_link[:200])
    else:
        print("\n❌ 未找到音訊連結")
        print("\n檢查 HTML 中是否包含 'mime=audio':")
        if 'mime=audio' in html_content:
            print("✓ HTML 中包含 'mime=audio'")
            # 找出所有包含 mime=audio 的位置
            import re
            matches = re.findall(r'href="([^"]*mime=audio[^"]*)"', html_content)
            print(f"找到 {len(matches)} 個匹配項")
            if matches:
                print(f"第一個匹配: {matches[0][:100]}...")
        else:
            print("✗ HTML 中不包含 'mime=audio'")


if __name__ == "__main__":
    test_extraction()
