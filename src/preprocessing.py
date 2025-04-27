"""
Corrects errors in the OCR process.
Errors in word boundaries (whether words are split or concatenated together) are corrected using Word Segment
Spelling is corrected using JamSpell
Initial Capitals (the large decorative capital letters which begin an article, commonly seen in magazines) are often 
scanned as separate text-blocks; these are detected and concatenated to the rest of their articles
Word Segment cannot handle punctuation or capital letters, these are removed and then replaced 
while anticipating the change in word boundaries.
"""

import regex as re
from textwrap import wrap 
from itertools import zip_longest

import jamspell
import wordsegment
from utils import load_config

spell_checker = None
config = None

punctuation_non_apostrophe = re.compile(r'[ ]?[^a-zA-Z\s’]+[ ]?|\n')
  # underscores, non-latin characters, all including spacing, faster, includes line-breaks to help segmentation (removed later)

remove_line_hyphenation = re.compile(r'[-\xad][ ]?\n') # matches words split by a line break
reduce_whitespace = re.compile(r'[\s_]+') # matches multiple spaces, newlines or underscores -> replace with single space

paragraph_break = re.compile(r'([\.”])\n([A-Z“])')
remove_paragraph_break = re.compile(config['paragraph_break_placeholder'])
reinsert_paragraph_break = re.compile('\1' + config['paragraph_break_placeholder'] + '\2')


config['paragraph_break_placeholder']
def __init__(self):
  self.spell_checker = jamspell.TSpellCorrector()
  self.spell_checker.LoadLangModel('en.bin')
  wordsegment.load()
  self.config = load_config()

def remove_initial_capitals(page_df):
  def is_inside_block(b1, b2): #Is the centre of block1 inside block2?
    centre_x = (b1['right'] + b1['left'])//2
    centre_y = (b1['bottom'] + b1['top'])//2
    return b2['left'] < centre_x < b2['right'] and b2['top'] < centre_y < b2['bottom']

  initial_caps = []
  for i,row in page_df.iterrows():
    if len(row['text'].strip())==1:
      initial_caps.append(row)
      page_df.drop(labels=i, axis=0, inplace=True)

  for initial in initial_caps:
    for i,row in page_df.iterrows():
      if is_inside_block(initial, row):
        page_df.at[i,'text'] = initial['text'].strip() + row['text'] # Add initial capital to text
        break
  return page_df

def fix_spacing_errors(text):
  punc = re.findall(punctuation_non_apostrophe, text) # Wordsegment doesn't work on punctuation -> removed before and added back after
  # wrap used to divide words into 200-char pieces, without splitting word boundaries
  words = [
      ' '.join(wordsegment.segment(s))
      if len(s) < config['wordsegment_max_limit']
      else ' '.join([' '.join(wordsegment.segment(ss)) for ss in wrap(s, config['wordsegment_max_limit'])])
    for s in re.split(punctuation_non_apostrophe, text) # Split text block by punctuation
  ]
  punc = [p if p!='\n' else ' ' for p in punc] # filter out line-breaks
  uncapitalized = ''.join([(w or '')+(p or '') for w,p in zip_longest(words, punc)])

  # Wordsegment removes all capitalisation -> detect positions of capital letters in original string and reinsert in corrected one
  caps = set()
  apo,apo2 = [],[] #index of apostrophes, in string with no spaces and corrected-spaces respectively

  i = 0 #index of non-spacing characters
  for c in text:
    if c=='’':
      apo.append(i)
    if c.isspace() or c=='’':
      continue
    i+=1
    if c.isupper():
      caps.add(i)

  capitalized = list(uncapitalized)
  i = 0
  for j,c in enumerate(uncapitalized):
    if c.isspace():
      continue
    i += 1
    if i in caps:
      capitalized[j] = c.capitalize()
    if i in apo:
      apo2.append(j)

  [capitalized.insert(idx+1,'’') for idx in reversed(apo2)]
  return ''.join(capitalized)

def process_text(text):
  text = re.sub(remove_line_hyphenation, '', text)
  text = re.sub(paragraph_break, r'\1&&&\2', text)
  text = re.sub(reduce_whitespace, ' ', text).strip()

  text = fix_spacing_errors(text)
  text = spell_checker.FixFragment(text)

  text = re.sub(reinsert_paragraph_break, '\n\n', text).strip()
  return text

def preprocessing(df):
  df.groupby(['pdf_file','page_number'], group_keys=False).apply(remove_initial_capitals).dropna()
  df['text'] = df.apply(lambda row: process_text(row['text']), axis=1)
  return df