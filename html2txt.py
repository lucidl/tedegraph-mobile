import requests
from bs4 import BeautifulSoup
import bs4
import nltk.util
import re
import nltk
import os
import codecs

images_dict = {}

def node_to_sentences(node):
  # converts html node (tag) to list of sentences

  if node is None:
    return []

  # remove uninteresting tags
  for t in node.find_all(["script", "style"]):
    t.decompose() # t.extract() is similar method 
  t = node.find("div", id = "toc")
  t.decompose()
  for t in node.find_all("table", class_ = "infobox"):
    img = t.find("img")
    if img:
        t.replaceWith(img)
    else:
        t.decompose()
  for t in node.find_all("div", class_ = "reflist"):
    t.decompose()
  for t in node.find_all("span", class_ = "mw-editsection"):
    t.decompose()
  

  for idx, img in enumerate(node.find_all("img")):
      img_key = "tdg_img_%03d" % idx 
      img.replaceWith(img_key)
      images_dict[img_key] = img["src"]

  all_nav_strings = [x for x in node.find_all(text=True) if x.strip() != "" if not type(x) is bs4.Comment]
  
  buffer = ""
  tokenized_strings = []
  for idx, nav_s in enumerate(all_nav_strings): # before it was enumerating node.stripped_strings
    s = nav_s.strip()
    s = s.replace("\r", "")

    try:
      s_next = all_nav_strings[idx + 1] # next navigable string
    except:
      s_next = None

    # we add string s to the buffer
    if s.startswith(",") or s.startswith(".") or buffer == "":
      buffer += s
    else:
      buffer += " " + s

    # tokenize the content of the buffer and empty the buffer.
    if s.endswith(".") or s_next is None or separate_strings(nav_s, s_next):
      # nav_s and s_next will be splitted
      tokenizer = nltk.data.load('nltk:tokenizers/punkt/english.pickle')
      buffer = buffer.replace("\n", " ")
      buffer = re.sub(" +", " ", buffer) # one or more spaces replace with one space
      sentences = tokenizer.tokenize(buffer)
      for sen in sentences:
        tokenized_strings.append(sen)
      buffer = ""

  return tokenized_strings

def separate_strings(s1, s2):
  onlys1 = [x.name for x in s1.parents if not x in s2.parents] # nodes only over s1
  onlys2 = [x.name for x in s2.parents if not x in s1.parents] # nodes only over s2
  # list of tags, that will let s1 and s2 splitted
  separatingTags = [ "h1", "h2", "h3", "h4", "h5", "h6", "h7", "li", "ol", "ul", "table", "tr", "th", "td", "div", "p", \
                     "dl", "dt", "dd"]
  for x in separatingTags:
    if x in onlys1 or x in onlys2:
      return True
  return False

def get_soup_from_url(url):
  if url.startswith('http'):
    html = requests.get(url, timeout=5).content
    soup = BeautifulSoup(html, features = "html.parser")
  return soup

def save_article(url, title, sentences):

  if not os.path.exists(title):
      os.makedirs(title)

  file_name = "0000000.txt"

  i = 0  # number of file

  pattern = re.compile("(tdg_img_\d{3})")

  for sentence in sentences:
    match = pattern.match(sentence)
    if match:
      img_url = images_dict[match.group(1)]
      img_extension = img_url.split(".")[-1].split("/")[0]
          
      try:
          img_file_name = "%07d." % i + img_extension
          if url.startswith("https") and not img_url.startswith("https"):
              r = requests.get("https:" + img_url)
          elif url.startswith("http") and not img_url.startswith("http"):
              r = requests.get("http:" + img_url)
          else:
              r = requests.get(img_url)
          file_name = "%07d.txt" % i 
          with open(os.path.join(title, img_file_name), "wb") as f:
              f.write(r.content)
      except Exception as e:
          continue
      i = i + 1
      continue

    with codecs.open(os.path.join(title, file_name), "a", encoding="utf-8") as f:
      f.write(sentence + "\n")
