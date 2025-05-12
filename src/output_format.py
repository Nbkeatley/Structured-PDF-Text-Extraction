"""
Converts the structured text data into human- and machine-readable .TXT and .DOCX format
Orders each page in terms of Title > Author name (if known) > Subheading (if present) > Article Body
Paragraph breaks are preserved from the original text
Output format:
"""

"""
-----------------------------------------------------
Article title:  <TITLE>
Author: <AUTHOR NAME>
Summary: <SUBHEADING>

<ARTICLE BODY>
"""
import regex as re
from utils import config

DIVIDING_LINE = '\n-----------------------------------------------------\n'
config = load_config()

def df_to_string(text_df, separator='\n\n'):
  return separator.join(text_df['text'].tolist())

def df_to_txt(df, OUTPUT_PATH):
  pdf_file = df['pdf_file'].head(1).values[0]
  text = df_to_string(df[df['pdf_file']==pdf_file])
  with open(OUTPUT_PATH+f'/{pdf_file}.txt', 'w', encoding='utf-8') as write_file:
    write_file.write(text)

def df_issue_to_docx(df, OUTPUT_PATH):
  pdf_file = df['pdf_file'].head(1).values[0]
  text = df_to_string(df[df['pdf_file']==pdf_file])
  with open(OUTPUT_PATH+f'/{pdf_file}.docx', 'w', encoding='utf-8') as write_file:
    write_file.write(text)

def format_page_df_to_string(df):
  title = df_to_string( df[df['heading_type']==0], separator=' ' ) if any(df['heading_type']==0) else ''
  subheading = df_to_string( df[df['heading_type']==1], separator=' ' )
  article_text = df_to_string(df[df['heading_type']==2])

  if not title: # no title on this page -> no article starting on this page
    return f"""{DIVIDING_LINE + 'Quote: ' + subheading + DIVIDING_LINE if subheading else ''}+{article_text}"""
    #Previously used Author for this, Titles works just as well in all 12939 pages with titles, with the exception of 42 cases

  return f"""
{DIVIDING_LINE}
Article title: {title}
{DIVIDING_LINE}

Author: {df['author'].tolist()[0]}
{'Summary: '+subheading if subheading else ''}{config['paragraph_break_placeholder']}

{article_text}
"""

def df_to_formatted_docx(df, OUTPUT_PATH):
  pdf_file = df['pdf_file'].values[0]
  # if an author, then do formatting, otherwise just df_to_string
  text = '\n'.join( df[df['not_header_footer']==True].groupby('page_number').apply(format_page_df_to_string).tolist() )

  text = re.sub(r'([a-z,”])\n+([a-z])', r'\1 \2', text)
    # When sentences move across pages or blocks, (detected by lack of full stop or Capital letter) -> join together
  text = re.sub(config['paragraph_break_placeholder'], '', text)

  with open(OUTPUT_PATH+f'/{pdf_file}.docx', 'w', encoding='utf-8') as write_file:
    write_file.write(text)
