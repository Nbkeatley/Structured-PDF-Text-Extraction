from pathlib import Path
import logging

from ocr import pdf_to_ocr_scanned_df
from preprocessing import preprocessing
from detect_structure_elements import classify_heading_type, remove_headers_footers
from detect_page_layout import detect_page_layout
from ner import detect_authors
from output_format import df_to_formatted_docx
from utils import load_config

def process_pdf_pipeline(pdf_file_path):
  df = pdf_to_ocr_scanned_df(pdf_file_path)
  df = preprocessing(df)
  df = remove_headers_footers(df)
  df = classify_heading_type(df)
  df = detect_page_layout(df)
  df = detect_authors(df)
  df.sort_values(by=['pdf_file', 'page_number', 'heading_type', 'column_position', 'centre_y'], inplace=True)
  df.groupby('pdf_file').apply(df_to_formatted_docx)

def main():
  logging.basicConfig(level=logging.INFO)
  config = load_config()
  INPUT_DIR, OUTPUT_DIR = Path(config['input_dir']), Path(config['output_dir'])
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  pdf_file_paths = sorted(list(INPUT_DIR.glob('*.pdf')))

  logging.info(f"Scanning {len(pdf_file_paths)} PDF files: {pdf_file_paths}")
  for pdf_file_path in pdf_file_paths:
    process_pdf_pipeline(pdf_file_path)

if __name__ == "__main__":
  main()