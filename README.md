# Structured-PDF-Text-Extraction
OCR-, LLM- and NLP-Based automated pipeline for extracting structured text from print media. This system leverages deep learning models and data analysis as well as advanced text processing to convert PDFs into both human- and machine-readable formats. Free and Open Source software (FOSS) is used whenever possible. Worked closely with stakeholders to 

# Key features include:
- OCR using Meta's Tesseract model, enhanced using image and text preprocessing
- Detectron2 and PubLayNet-based layout detection
- Statistically-informed classification of page elements
- Customised template-matching algorithm for ordering text-boxes
- Author name detection using NER based on Google's BERT model
- Output as Pandas dataframe, .docx, and .txt formats

# Pipeline Description

OCR Module (ocr.py):
- Extracts images from PDF pages and enhances quality via unsharp masking and adaptive thresholding
- Uses Meta's Detectron2 model to predict boundaries and coordinates of text blocks (excluding figures)
- Using these boundaries, text is extracted from each block using Google's LSTM-based Tesseract OCR model
- Outputs a Pandas DataFrame with text content, bounding box coordinates, and other metadata

Text Processing (preprocessing.py):
- Anticipates and corrects corrupted text due to the OCR process; errors in spacing (whether added or removed) corrected using WordSegment
- Output is spell-checked using JamSpell
- Words which are hyphenated across linebreaks are removed
- Initial capital letters (stylised large letters often seen in print magazines) are detected and merged with their associated sentences

Heading Classification (detect_subheadings.py):
- Removes headers and footers (e.g. page numbers) based on vertical cut-offs - calculated from statistical analysis of a hand-labelled dataset
- Calculates relative font sizes to classify text as titles, subheadings, or body
- Uses Z-scores against page and document-wide font statistics to account for variations in text stylisation

Page Layout Analysis (detect_page_layout.py):
- Orders text blocks on page despite unknown layout
- Uses a custom algorithm to evaluate multiple possible layouts (e.g. 2, 3, 4 columns) and assigns text-blocks to the layout with minimal positioning error

Author Detection (ner.py):
- Uses a BERT-based Named Entity Recognition model to identify person entities in the text
- Matches detected names against a precompiled list using fuzzy matching.

Output Formatting (output_format.py):
- Groups and structures text into articles with titles, authors, summaries, and text-body/content
- Outputs formatted documents in .docx or .txt with preserved paragraph breaks for ease of reading

# Requirements
Ensure that all dependencies using setup.sh
