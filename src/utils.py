import logging
import pickle
import fitz
import yaml

def load_model(model, model_name):
  try:
    return model
  except OSError as e:
    logging.error(f"Model files for {model_name} not found {e}")
  except Exception as e:
    logging.exception(f"Unexpected error loading model {model_name}: {e}")
  return None

def load_fitz_file(file_path):
  try:
    file = fitz.open(file_path)
    logging.info(f"File loaded {file_path}")
    if file.is_repaired:
      logging.warning(f"PyMuPDF needed to repair PDF when loading: {file_path} \n {fitz.TOOLS.mupdf_warnings()}")
    return file
  except FileNotFoundError:
    logging.error(f"File not found in path {file_path}")
  except RuntimeError as e:
    logging.error(f"Runtime error while loading file {file_path}: {e}")
  except Exception as e:
    logging.exception(f"Unexpected error loading file {file_path}: {e}")
  return None

def load_pkl_file(file_path):
  try:
    with open(file_path, 'rb') as f:
      file = pickle.load(f)
    logging.info(f"File loaded {file_path}")
    return file
  except FileNotFoundError:
    logging.error(f"File not found in path {file_path}")
  except pickle.UnpicklingError:
    logging.error(f"Failed to unpickle file at {file_path}")
  except Exception as e:
    logging.exception(f"Unexpected error loading file {file_path}: {e}")
  return None

def load_config():
  with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
  return config