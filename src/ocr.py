"""
Converts PDFs of scanned images to a structured Pandas Dataframe of text
Images are acquired with PyMuPDF and filtered via unsharp masking, and adaptive thresholding.
Text and their boundaries are detected using Detectron2 and the text strings are extracted using TesseractOCR
Metadata is retained for further processing and layout detection (e.g. bounding box XY coordinates)
"""

from io import BytesIO
from PIL import Image

import fitz
import numpy as np
import pandas
from layoutparser import Detectron2LayoutModel, TesseractAgent, Layout
import cv2
from pathlib import Path
import logging

from utils import load_model, load_fitz_file, load_config

layout_detecting_model = None
ocr_agent = None
mat = None
config = None

def __init__(self):
  self.config = load_config()

  self.layout_detecting_model = load_model(Detectron2LayoutModel(
    config_path=self.config['detectron2']['path'],
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
    label_map=self.config['detectron2']['label_map']
  ), model_name='Detectron2 Layout Model')
  self.ocr_agent = load_model(TesseractAgent(
    languages='eng', 
    config=self.config['ocr']['tesseract_config']  # speed up OCR by not checking for inverted text
  ), model_name='Tesseract Agent OCR model')
  self.mat = fitz.Matrix(300 / 72, 300 / 72)  # sets Zoom Factor to 300 dpi

def page_to_img(page_obj):
  pix = page_obj.get_pixmap(matrix=mat) 
  img = pix.tobytes(output='png')
  return np.array(Image.open(BytesIO(img)))

#Enlarges and converts to black-and-white for more effective OCR
def pre_process_img(img):
  img = cv2.resize(img, (0,0), fx=config['ocr']['scale_factor'], fy=config['ocr']['scale_factor']) 
  img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


#Note: larger Sigma value allows greater variance around the mean, leading to more noise
def unsharp_mask(img):
  GAUSSIAN_BLUR_MASK = cv2.GaussianBlur(img, (0, 0), sigmaX=config['ocr']['gaussian_blur_sigma'])
  img = cv2.addWeighted(img, 2.0, GAUSSIAN_BLUR_MASK, -1.0, gamma=0)
  # The blur is subtracted from the original image using the '2.0' and '-1.0' weightings
  return img

def thresholding(img):
  img_macro_details = cv2.adaptiveThreshold(
    img, 
    255, 
    cv2.ADAPTIVE_THRESH_MEAN_C, 
    cv2.THRESH_BINARY, 
    blockSize=config['ocr']['adaptive_threshold']['macro_block_size'], 
    C=config['ocr']['adaptive_threshold']['macro_C'])
  kernel = np.ones((5,5), np.uint8) 
  img_macro_details = cv2.dilate(img_macro_details, kernel, iterations=5)

  get_block_size = lambda img: int(np.shape(img)[0]/300)*10 | 1
  # Thresholding's performance is dependent on the block size, which is sensitive to image size
  # e.g. size=11 works well for 3300-pixel-wide image
  # Block size must be an odd number, this is ensured using the final "| 1" binary operation
  
  img_micro_details = cv2.adaptiveThreshold(
    img, 
    255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 
    blockSize=get_block_size(img), 
    C=config['ocr']['adaptive_threshold']['micro_C']) 
  # C determines how much darker a pixel should be (compared to the average neighbouring pixel) to be retained as a detail
    
  img = cv2.bitwise_and(img_micro_details, img_macro_details)  #combine images
  return img



def img_to_text_blocks(img):
  # Crops the original image to each bounding box of a text-block
  # Adds padding to improve robustness, in case any words are partially cut-off
  PAD_SIZE = config['ocr']['pad_size']
  def bounding_boxes_to_text(box, img):
    text = ocr_agent.detect(
      box.pad(left=PAD_SIZE, right=PAD_SIZE, top=PAD_SIZE, bottom=PAD_SIZE).crop_image(img)
    )
    return box.set(text=text, inplace=True)
  layout_result = layout_detecting_model.detect(img)
  bounding_boxes_list = Layout([b for b in layout_result if b.type != "Figure"]) # 'Figure' == image
  text_blocks = [bounding_boxes_to_text(box, img) for box in bounding_boxes_list]
  return text_blocks

# Converts from HOCR text-block format to a dict with attributes more amenable for processing and classifying
def format_text_blocks(text_blocks, pdf_filename, page_number):
  return [{
    'left': int(text_block.block.x_1),
    'top': int(text_block.block.y_1),
    'bottom': int(text_block.block.y_2),
    'right': int(text_block.block.x_2),
    'pdf_file': pdf_filename,
    'page_number': page_number,
    'text': text_block.text
  } for text_block in text_blocks]

def pdf_page_to_text_blocks(pdf_page, pdf_filename, page_number):
  img = page_to_img(pdf_page)
  img = pre_process_img(img)
  img = unsharp_mask(img)
  img = thresholding(img)
  text_blocks = img_to_text_blocks(img)
  text_blocks = format_text_blocks(text_blocks, pdf_filename, page_number)
  return text_blocks

def pdf_to_ocr_scanned_df(pdf_file_path):
  pdf_filename = Path(pdf_file_path).stem
  df = pandas.DataFrame()
  pdf_file = load_fitz_file(pdf_file_path)

  for page_number,_ in enumerate(pdf_file):
    page = pdf_file[page_number]
    text_blocks = pdf_page_to_text_blocks(page, pdf_file_path, page_number)
    df = pandas.concat([df, pandas.DataFrame(text_blocks)])
    logging.info(f'Page {page_number+1} in {pdf_filename} completed')
  pdf_file.close()
  df['centre_x'] = df.apply(lambda row: (row['left'] + row['right'])//2, axis=1)
  df['centre_y'] = df.apply(lambda row: (row['bottom'] + row['top'])//2, axis=1)
  
  return df
  
