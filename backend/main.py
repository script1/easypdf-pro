from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import shutil
import uuid
from typing import List
import zipfile
from pypdf import PdfWriter, PdfReader
import fitz  # PyMuPDF
from pdf2docx import Converter

app = FastAPI()

# Configure CORS to allow any origin (for public access)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def read_root():
    return {"message": "EasyPDF Backend is Running"}


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the server.
    Validates that the file is a PDF.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    saved_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    return {
        "filename": file.filename,
        "file_id": file_id,
        "content_type": file.content_type,
        "path": file_path,
        "message": "File uploaded successfully",
    }


@app.post("/convert/pdf-to-word/")
async def convert_pdf_to_word(file_id: str):
    """
    Convert a previously uploaded PDF file to Word (.docx).
    """
    files = os.listdir(UPLOAD_DIR)
    target_file = None
    for f in files:
        if f.startswith(file_id) and f.endswith(".pdf"):
            target_file = f
            break

    if not target_file:
        raise HTTPException(status_code=404, detail="File not found")

    pdf_path = os.path.join(UPLOAD_DIR, target_file)
    docx_filename = f"{file_id}.docx"
    docx_path = os.path.join(UPLOAD_DIR, docx_filename)

    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    return {
        "message": "Conversion successful",
        "docx_filename": docx_filename,
        "download_url": f"/download/{docx_filename}",
    }


@app.post("/merge/")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    """
    Merge multiple PDF files into one.
    """
    if not files or len(files) < 2:
        raise HTTPException(
            status_code=400, detail="Please upload at least 2 PDF files."
        )

    merger = PdfWriter()
    temp_files = []
    input_streams = []

    try:
        for file in files:
            if file.content_type != "application/pdf":
                raise HTTPException(
                    status_code=400, detail=f"File {file.filename} is not a PDF."
                )

            temp_id = str(uuid.uuid4())
            temp_path = os.path.join(UPLOAD_DIR, f"{temp_id}.pdf")

            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            temp_files.append(temp_path)

            f = open(temp_path, "rb")
            input_streams.append(f)
            merger.append(f)

        merged_filename = f"merged_{uuid.uuid4()}.pdf"
        merged_path = os.path.join(UPLOAD_DIR, merged_filename)

        with open(merged_path, "wb") as f_out:
            merger.write(f_out)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")
    finally:
        for f in input_streams:
            try:
                f.close()
            except Exception:
                pass

        for path in temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    return {
        "message": "Merge successful",
        "merged_filename": merged_filename,
        "download_url": f"/download/{merged_filename}",
    }


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


@app.post("/split/")
async def split_pdf(file: UploadFile = File(...), pages: str = Form(None)):
    """
    Split a PDF into multiple PDF files. Support page selection.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    task_id = str(uuid.uuid4())
    input_filename = f"split_input_{task_id}.pdf"
    input_path = os.path.join(UPLOAD_DIR, input_filename)

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    zip_filename = f"split_{task_id}.zip"
    zip_path = os.path.join(UPLOAD_DIR, zip_filename)

    generated_files = []

    try:
        selected_pages = []
        if pages:
            try:
                selected_pages = [
                    int(p.strip()) for p in pages.split(",") if p.strip().isdigit()
                ]
            except ValueError:
                pass

        with open(input_path, "rb") as f_in:
            reader = PdfReader(f_in)
            total_pages = len(reader.pages)

            if total_pages < 1:
                raise HTTPException(status_code=400, detail="PDF has no pages.")

            if not selected_pages:
                selected_pages = list(range(total_pages))

            pdf_paths = []

            for i in selected_pages:
                if i < 0 or i >= total_pages:
                    continue

                writer = PdfWriter()
                writer.add_page(reader.pages[i])

                page_filename = f"page_{i+1}.pdf"
                page_path = os.path.join(UPLOAD_DIR, f"{task_id}_{page_filename}")

                with open(page_path, "wb") as f_out:
                    writer.write(f_out)

                generated_files.append(page_path)
                pdf_paths.append((page_path, page_filename))

            # Decide on output format
            if len(pdf_paths) == 1:
                single_path, single_name = pdf_paths[0]
                generated_files.remove(single_path)

                return {
                    "message": "Split successful",
                    "zip_filename": single_name,
                    "download_url": f"/download/{os.path.basename(single_path)}",
                }
            else:
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for p_path, p_name in pdf_paths:
                        zipf.write(p_path, arcname=p_name)

                return {
                    "message": "Split successful",
                    "zip_filename": zip_filename,
                    "download_url": f"/download/{zip_filename}",
                }

    except Exception as e:
        print(f"Error splitting PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")
    finally:
        for path in generated_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception:
            pass


@app.post("/convert/pdf-to-jpg/")
async def convert_pdf_to_jpg(file: UploadFile = File(...), pages: str = Form(None)):
    """
    Convert a PDF into JPG images. Support page selection.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    task_id = str(uuid.uuid4())
    input_filename = f"jpg_input_{task_id}.pdf"
    input_path = os.path.join(UPLOAD_DIR, input_filename)

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    zip_filename = f"images_{task_id}.zip"
    zip_path = os.path.join(UPLOAD_DIR, zip_filename)

    generated_files = []

    try:
        doc = fitz.open(input_path)
        total_pages = len(doc)

        selected_pages = []
        if pages:
            try:
                selected_pages = [
                    int(p.strip()) for p in pages.split(",") if p.strip().isdigit()
                ]
            except ValueError:
                pass

        if not selected_pages:
            selected_pages = list(range(total_pages))

        img_paths = []

        for i in selected_pages:
            if i < 0 or i >= total_pages:
                continue

            page = doc[i]
            pix = page.get_pixmap(dpi=150)
            img_filename = f"page_{i+1}.jpg"
            img_path = os.path.join(UPLOAD_DIR, f"{task_id}_{img_filename}")

            pix.save(img_path)
            generated_files.append(img_path)
            img_paths.append((img_path, img_filename))

        doc.close()

        if len(img_paths) == 1:
            single_path, single_name = img_paths[0]
            generated_files.remove(single_path)

            return {
                "message": "Conversion successful",
                "zip_filename": single_name,
                "download_url": f"/download/{os.path.basename(single_path)}",
            }
        else:
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for p_path, p_name in img_paths:
                    zipf.write(p_path, arcname=p_name)

            return {
                "message": "Conversion successful",
                "zip_filename": zip_filename,
                "download_url": f"/download/{zip_filename}",
            }

    except Exception as e:
        print(f"Error converting PDF to JPG: {e}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        for path in generated_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception:
            pass


@app.post("/protect/")
async def protect_pdf(file: UploadFile = File(...), password: str = Form(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")

    task_id = str(uuid.uuid4())
    input_filename = f"protect_input_{task_id}.pdf"
    input_path = os.path.join(UPLOAD_DIR, input_filename)

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    protected_filename = f"protected_{task_id}.pdf"
    protected_path = os.path.join(UPLOAD_DIR, protected_filename)

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)

        with open(protected_path, "wb") as f_out:
            writer.write(f_out)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Protection failed: {str(e)}")
    finally:
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception:
            pass

    return {
        "message": "Protection successful",
        "protected_filename": protected_filename,
        "download_url": f"/download/{protected_filename}",
    }


@app.post("/compress/")
async def compress_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    task_id = str(uuid.uuid4())
    input_filename = f"compress_input_{task_id}.pdf"
    input_path = os.path.join(UPLOAD_DIR, input_filename)

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    compressed_filename = f"compressed_{task_id}.pdf"
    compressed_path = os.path.join(UPLOAD_DIR, compressed_filename)

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        for page in writer.pages:
            page.compress_content_streams()

        writer.compress_identical_objects()

        with open(compressed_path, "wb") as f_out:
            writer.write(f_out)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")
    finally:
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception:
            pass

    return {
        "message": "Compression successful",
        "compressed_filename": compressed_filename,
        "download_url": f"/download/{compressed_filename}",
    }
