"""
Detects Author names within article text for structured, meaningful outputs
Uses a BERT-based Named-Entity-Recognition (NER) language model
Can additionally match detected names against a given list using fuzzy matching and trie-based search.
"""
import re
from torch import cuda
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from pytrie import SortedStringTrie as Trie
from Levenshtein import ratio

from utils import load_pkl_file, load_model, load_config

AUTHOR_NAMES_FILEPATH = 'data/author_names.pkl'
alphabetic_chars = re.compile(r'[a-zA-Z]')
ner_classifier = None
author_names_list = None
author_names_trie = None
config = None





def __init__(self):
  self.config = load_config()
  tokenizer = load_model(AutoTokenizer.from_pretrained(config['ner']['dslim/bert-base-NER']), 'BERT Tokenizer')
  device = "cuda:0" if cuda.is_available() else "cpu"
  model = load_model(AutoModelForTokenClassification.from_pretrained(config['ner']['dslim/bert-base-NER']).to(device), 'BERT base model')
  self.ner_classifier = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy='average')

  author_names_df = load_pkl_file(config['author_names_filepath'])
  self.author_names_trie = Trie({remove_spaces(name):name for _,name in author_names_df['fullname'].iteritems()})
  self.author_names_list = sorted(author_names_df['fullname'].to_list())

def remove_spaces(string):
  return re.sub(' ','', string).lower()

def spell_check_author_name(author):
  for author_true in author_names_list:
    if ratio(author_true, author, score_cutoff=config['ner']['score_cutoff']):
      return author_true
  author_name = author_names_trie.longest_prefix_value(remove_spaces(author), default=author)
  return author_name

def df_to_string(text_df, separator='\n\n'):
  return separator.join(text_df['text'].tolist())

def safe_get_first_elem(lst, if_none=''):
  return next(iter(lst[0:]), if_none)

def detect_author_in_page(page_df): #Assume one article maximum per page (or none)
  if page_df[page_df['title_subheading_article']==0].empty: #if no title on page, skip
    page_df['author'] = ''
    return page_df
  text = df_to_string(page_df[page_df['title_subheading_article']<2].sort_values(by='title_subheading_article'), separator='. ')
  if not re.search(alphabetic_chars, text): # NER fails on input without any alphabetic characters
    page_df['author'] = ''
    return page_df
  names = [tag['word'] for tag in ner_classifier(text.title()) if tag['entity_group']=='PER'] 
    # More effective performance when only the first letter is capitalised, hence title()
  first_name_in_text = safe_get_first_elem(names)
  page_df['author'] = spell_check_author_name(first_name_in_text)
  return page_df

def detect_authors(df):
  df = df.groupby(['pdf_file', 'page_number']).apply(detect_author_in_page) #detect author
  return df