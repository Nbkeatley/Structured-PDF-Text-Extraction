"""
Text in multiple columns (often occurring in newspapers or magazines) can pose unique problems for ordering text on a page,
especially when the number of columns are unknown and must be inferred.

This method assigns text-blocks to columns, based on the coordinates of each block's centre-point.
Multiple possible layouts are evaluated (2, 3, or 4 columns) and selects the layout with the least error 
(i.e. each block's horizontal distance from ideal column position)

(Note that PDF coordinates follow Cartesian convention; (0,0)/Origin is in left and bottom of the page)
Uses statistical analysis of a hand-labelled dataset (N = 21,000) to determine column spacing.
"""


from utils import load_config

config = load_config()
column_centres = config['column_centres']
col_width_margins = config['assign_column']
UNSORTED_COLUMN_VALUE = 10


#'Centre' = X-coordinate of centre of text-box
#Firstly subtracts the left-hand margin (e.g. 30 pixels), 
#Then divides by spacing of columns (e.g. 210px for 2-columns, 130 for 3-cols)
assign_column = {
  'double_col': lambda centre: min(1, centre//col_width_margins['double_col_width']),
  'triple_col': lambda centre: min(2, (centre-col_width_margins['triple_col_margin'])//col_width_margins['triple_col_width']),
  'quadruple_col': lambda centre: min(3, (centre-col_width_margins['quadruple_col_margin'])//col_width_margins['quadruple_col_width'])
}


def assign_layout_ordering_to_page_df(page_df):
  error = {layout: 0 for layout in column_centres.keys()}
  for layout in column_centres.keys():
    page_df[layout] = UNSORTED_COLUMN_VALUE

  for i,text_block in page_df.iterrows():
    for layout in column_centres.keys():
      predicted_column = assign_column[layout](text_block['centre_x'])
      page_df.at[i, layout] = predicted_column
      error[layout] += abs(text_block['centre_x'] - column_centres[layout][predicted_column])

  best_layout = sorted(error, key=error.get)[0]
  page_df['column_position'] = page_df[best_layout]
  return page_df.drop(column_centres.keys(), axis=1)

def detect_page_layout(df):
  df = df.groupby(['pdf_file','page_number'], group_keys=False).apply(assign_layout_ordering_to_page_df)
  return df
