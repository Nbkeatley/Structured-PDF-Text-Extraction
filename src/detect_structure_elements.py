"""
Classifies text blocks as structure elements (e.g. title, article text, subheading, header, footer),
these are critical for ordering text within each page, and removing extraneous details such as page numbers.

Logical rules for classifying structure elements determined using insights from statistical analysis of dataset (N = 21,000)
Headers and footers are based on vertical coordinates of text-blocks
Titles are determined by the font-size of text
Subheadings (with a font-size smaller than titles but larger than regular text) is determined to be relatively larger 
than the average for each page, AND larger than average across the entire PDF.
The latter is calculated using the PDF's standard deviation, because PDF differ widely in their variance of font-size.
"""

from utils import load_config

config_struct = load_config()['detect_structure']

def remove_headers_footers(df):
  is_not_header_or_footer = lambda row: all(row['top']<=config_struct['header_cutoff'], row['bottom']>=config_struct['footer_cutoff'])
  df = df[df.apply(is_not_header_or_footer, axis=1)]
  return df

# Font-size calculated by dividing text-box area by text-length (assuming the text fills the text-box equally)
def compute_font_size(row):
  return ((row['right'] - row['left']) * (row['bottom'] - row['top'])) // max(1, len(row['text']))

def compute_pdf_font_stats(df):
  chars_per_text_box = df['text'].apply(len)
  weighted_avg = ( df['font_size'] * chars_per_text_box ).sum() // chars_per_text_box.sum()
    # average is weighted by the length of each text box
  df['pdf_font_size_avg'] = weighted_avg
  df['pdf_font_size_std'] = df['font_size'].std()
  return df
  
def compute_page_font_size_avg(page_df): #weighted average, by number of characters
  chars_per_text_box = page_df['text'].apply(len)
  page_df['page_font_size_avg'] = sum(page_df['font_size'] * chars_per_text_box ) // chars_per_text_box.sum()
  return page_df

def classify_heading_type_in_text_block(row):
  font_size_Z_score_of_pdf_avg = round((row['font_size'] - row['pdf_font_size_avg']) / row['pdf_font_size_std'], 2) 
  #font size of this text block, relative to the average for this PDF
  if (row['font_size'] > config_struct['title_font_size_cutoff']):
    return 0 #title
  elif (row['font_size'] > row['page_font_size_avg']) & (font_size_Z_score_of_pdf_avg >= config_struct['subheading_zscore_relative']):
    return 1 #sub-heading
  else:
    return 2 #article text

def classify_heading_type(df):
  df['font_size'] = df.apply(compute_font_size, axis=1)
  df = df.groupby(['pdf_file', 'page_number'], group_keys=False).apply(compute_page_font_size_avg) 
  df = df.groupby(['pdf_file'], group_keys=False).apply(compute_pdf_font_stats)
  df['heading_type'] = df.apply(classify_heading_type_in_text_block, axis=1)
  df.drop(['pdf_font_size_std', 'pdf_font_size_avg', 'page_font_size_avg'], axis=1, inplace=True)
  return df
