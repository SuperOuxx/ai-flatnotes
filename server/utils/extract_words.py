import re

def extract_first_word(text):
  """
  提取字符串中第一个连续的非标点符号字符串。

  Args:
    text: 输入的字符串。

  Returns:
    提取到的第一个字符串，如果不存在则返回None。
  """
  match = re.search(r"[^\W\d_]+", text)
  if match:
    return match.group(0)
  else:
    return None

def extract_all_words(text):
    """
    提取字符串中所有连续的非标点符号字符串。

    Args:
        text: 输入的字符串。

    Returns:
        一个包含所有提取到的字符串的列表。
    """
    return re.findall(r"[^\W\d_]+", text)

def choose_longest_word(text):
    words = extract_all_words(text)
    if not words:
      return ""
    return max(words, key=len)

def extract_first_quoted_string(s: str) -> str:
    """提取字符串中第一个被成对双引号包裹的字符串"""
    start = s.find('"')
    if start == -1:
        return None  # 没有左引号
    
    # 从左引号的下一个字符开始查找右引号
    end = s.find('"', start + 1)
    if end == -1:
        return None  # 没有右引号
    
    # 返回两个引号之间的内容
    return s[start + 1:end]


if __name__ == "__main__":
    # 示例用法
    text1 = "Hello, world!  This is a test."
    text2 = "123abc456def"
    text3 = "你好，世界！"
    text4 = ""
    text5 = " "

    print(f'"{text1}" 提取第一个单词: {extract_first_word(text1)}')
    print(f'"{text1}" 提取所有单词: {extract_all_words(text1)}')

    print(f'"{text2}" 提取第一个单词: {extract_first_word(text2)}')
    print(f'"{text2}" 提取所有单词: {extract_all_words(text2)}')

    print(f'"{text3}" 提取第一个单词: {extract_first_word(text3)}')
    print(f'"{text3}" 提取所有单词: {extract_all_words(text3)}')

    print(f'"{text4}" 提取第一个单词: {extract_first_word(text4)}')
    print(f'"{text4}" 提取所有单词: {extract_all_words(text4)}')

    print(f'"{text5}" 提取第一个单词: {extract_first_word(text5)}')
    print(f'"{text5}" 提取所有单词: {extract_all_words(text5)}')