from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import shutil
import uuid
from typing import List
import zipfile
from pypdf import PdfWriter, PdfReader
import fitz  # PyMuPDF
from pdf2docx import Converter
import asyncio
import time

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
FILE_EXPIRY_SECONDS = 3600  # 1 hour
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def cleanup_old_files():
    while True:
        await asyncio.sleep(1800)
        now = time.time()
        try:
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                try:
                    if os.path.isfile(file_path):
                        if now - os.path.getmtime(file_path) > FILE_EXPIRY_SECONDS:
                            os.remove(file_path)
                except Exception:
                    pass
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_old_files())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def is_valid_pdf(data: bytes) -> bool:
    return data[:5] == b'%PDF-'


def is_valid_image(content_type: str) -> bool:
    return content_type in {
        "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"
    }


async def read_file_bytes(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )
    return data


app = FastAPI(title="EasyPDF Pro API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────── UPLOAD ───────────────────────────

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "")[1] or ".pdf"
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    with open(file_path, "wb") as f:
        f.write(data)

    return {
        "filename": file.filename,
        "file_id": file_id,
        "content_type": file.content_type,
        "path": file_path,
        "message": "File uploaded successfully",
        "download_url": f"/download/{file_id}{ext}",
    }


# ─────────────────────────── MERGE ────────────────────────────

@app.post("/merge/")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least 2 PDF files.")

    merger = PdfWriter()
    temp_files = []

    try:
        for file in files:
            data = await read_file_bytes(file)
            if not is_valid_pdf(data):
                raise HTTPException(status_code=400, detail=f"{file.filename} is not a valid PDF.")
            temp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.pdf")
            with open(temp_path, "wb") as f:
                f.write(data)
            temp_files.append(temp_path)

        for path in temp_files:
            merger.append(path)

        merged_filename = f"merged_{uuid.uuid4()}.pdf"
        merged_path = os.path.join(UPLOAD_DIR, merged_filename)
        with open(merged_path, "wb") as f:
            merger.write(f)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")
    finally:
        merger.close()
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass

    return {
        "message": "Merge successful",
        "merged_filename": merged_filename,
        "download_url": f"/download/{merged_filename}",
    }


# ─────────────────────────── SPLIT ────────────────────────────

@app.post("/split/")
async def split_pdf(file: UploadFile = File(...), pages: str = Form(None)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"split_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    generated_files = []
    zip_filename = f"split_{task_id}.zip"
    zip_path = os.path.join(UPLOAD_DIR, zip_filename)

    try:
        with open(input_path, "rb") as f_in:
            reader = PdfReader(f_in)
            total_pages = len(reader.pages)

            selected_pages = []
            if pages:
                selected_pages = [
                    int(p.strip())
                    for p in pages.split(",")
                    if p.strip().isdigit() and 0 <= int(p.strip()) < total_pages
                ]
            if not selected_pages:
                selected_pages = list(range(total_pages))

            pdf_paths = []
            for i in selected_pages:
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                page_filename = f"page_{i + 1}.pdf"
                page_path = os.path.join(UPLOAD_DIR, f"{task_id}_{page_filename}")
                with open(page_path, "wb") as f_out:
                    writer.write(f_out)
                generated_files.append(page_path)
                pdf_paths.append((page_path, page_filename))

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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")
    finally:
        for path in generated_files:
            try:
                os.remove(path)
            except Exception:
                pass
        try:
            os.remove(input_path)
        except Exception:
            pass


# ─────────────────────── PDF → WORD ───────────────────────────

@app.post("/convert/pdf-to-word/")
async def convert_pdf_to_word(
    file_id: str = None,
    file: UploadFile = File(None),
):
    pdf_path = None
    temp_created = False

    if file_id:
        files = os.listdir(UPLOAD_DIR)
        target = next((f for f in files if f.startswith(file_id) and f.endswith(".pdf")), None)
        if not target:
            raise HTTPException(status_code=404, detail="File not found.")
        pdf_path = os.path.join(UPLOAD_DIR, target)
    elif file:
        data = await read_file_bytes(file)
        if not is_valid_pdf(data):
            raise HTTPException(status_code=400, detail="Invalid PDF file.")
        task_id = str(uuid.uuid4())
        pdf_path = os.path.join(UPLOAD_DIR, f"{task_id}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(data)
        temp_created = True
    else:
        raise HTTPException(status_code=400, detail="Provide file_id or upload a file.")

    task_id = str(uuid.uuid4())
    docx_filename = f"word_{task_id}.docx"
    docx_path = os.path.join(UPLOAD_DIR, docx_filename)

    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        if temp_created and pdf_path:
            try:
                os.remove(pdf_path)
            except Exception:
                pass

    return {
        "message": "Conversion successful",
        "docx_filename": docx_filename,
        "download_url": f"/download/{docx_filename}",
    }


# ─────────────────────── PDF → JPG ────────────────────────────

@app.post("/convert/pdf-to-jpg/")
async def convert_pdf_to_jpg(file: UploadFile = File(...), pages: str = Form(None)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"jpg_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    zip_filename = f"images_{task_id}.zip"
    zip_path = os.path.join(UPLOAD_DIR, zip_filename)
    generated_files = []

    try:
        doc = fitz.open(input_path)
        total_pages = len(doc)

        selected_pages = []
        if pages:
            selected_pages = [
                int(p.strip())
                for p in pages.split(",")
                if p.strip().isdigit() and 0 <= int(p.strip()) < total_pages
            ]
        if not selected_pages:
            selected_pages = list(range(total_pages))

        img_paths = []
        for i in selected_pages:
            page = doc[i]
            pix = page.get_pixmap(dpi=150)
            img_filename = f"page_{i + 1}.jpg"
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        for path in generated_files:
            try:
                os.remove(path)
            except Exception:
                pass
        try:
            os.remove(input_path)
        except Exception:
            pass


# ──────────────────── IMAGES → PDF ────────────────────────────

@app.post("/convert/images-to-pdf/")
async def images_to_pdf(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one image.")

    task_id = str(uuid.uuid4())
    temp_files = []
    output_filename = f"images_to_pdf_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        doc = fitz.open()
        for file in files:
            if not is_valid_image(file.content_type or ""):
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is not a supported image.",
                )
            data = await read_file_bytes(file)
            ext = os.path.splitext(file.filename or "")[1] or ".jpg"
            temp_path = os.path.join(UPLOAD_DIR, f"{task_id}_{uuid.uuid4()}{ext}")
            with open(temp_path, "wb") as f:
                f.write(data)
            temp_files.append(temp_path)

            img_doc = fitz.open(temp_path)
            pdf_bytes = img_doc.convert_to_pdf()
            img_doc.close()
            img_pdf = fitz.open("pdf", pdf_bytes)
            doc.insert_pdf(img_pdf)
            img_pdf.close()

        doc.save(output_path)
        doc.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass

    return {
        "message": "Images converted to PDF successfully",
        "output_filename": output_filename,
        "download_url": f"/download/{output_filename}",
    }


# ─────────────────────── PROTECT ──────────────────────────────

@app.post("/protect/")
async def protect_pdf(file: UploadFile = File(...), password: str = Form(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"protect_input_{task_id}.pdf")
    protected_filename = f"protected_{task_id}.pdf"
    protected_path = os.path.join(UPLOAD_DIR, protected_filename)

    with open(input_path, "wb") as f:
        f.write(data)

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(protected_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Protection failed: {str(e)}")
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass

    return {
        "message": "Protection successful",
        "protected_filename": protected_filename,
        "download_url": f"/download/{protected_filename}",
    }


# ─────────────────────── UNLOCK ───────────────────────────────

@app.post("/unlock/")
async def unlock_pdf(file: UploadFile = File(...), password: str = Form(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"unlock_input_{task_id}.pdf")
    output_filename = f"unlocked_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    with open(input_path, "wb") as f:
        f.write(data)

    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            if not reader.decrypt(password):
                raise HTTPException(status_code=401, detail="Incorrect password.")
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unlock failed: {str(e)}")
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass

    return {
        "message": "PDF unlocked successfully",
        "output_filename": output_filename,
        "download_url": f"/download/{output_filename}",
    }


# ─────────────────────── COMPRESS ─────────────────────────────

@app.post("/compress/")
async def compress_pdf(file: UploadFile = File(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"compress_input_{task_id}.pdf")
    compressed_filename = f"compressed_{task_id}.pdf"
    compressed_path = os.path.join(UPLOAD_DIR, compressed_filename)

    with open(input_path, "wb") as f:
        f.write(data)

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        for page in writer.pages:
            page.compress_content_streams()
        writer.compress_identical_objects()
        with open(compressed_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass

    return {
        "message": "Compression successful",
        "compressed_filename": compressed_filename,
        "download_url": f"/download/{compressed_filename}",
    }


# ─────────────────────── WATERMARK ────────────────────────────

@app.post("/watermark/")
async def add_watermark(
    file: UploadFile = File(...),
    text: str = Form(...),
    opacity: float = Form(0.3),
):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"wm_input_{task_id}.pdf")
    output_filename = f"watermarked_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    with open(input_path, "wb") as f:
        f.write(data)

    try:
        doc = fitz.open(input_path)
        for page in doc:
            rect = page.rect
            page.insert_text(
                fitz.Point(rect.width / 2 - 100, rect.height / 2),
                text,
                fontsize=48,
                color=(0.7, 0.7, 0.7),
                rotate=45,
                overlay=True,
            )
        doc.save(output_path)
        doc.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Watermark failed: {str(e)}")
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass

    return {
        "message": "Watermark added successfully",
        "download_url": f"/download/{output_filename}",
    }


# ─────────────────────── ROTATE ───────────────────────────────

@app.post("/rotate/")
async def rotate_pdf(
    file: UploadFile = File(...),
    angle: int = Form(...),
    pages: str = Form(None),
):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")
    if angle not in (90, 180, 270):
        raise HTTPException(status_code=400, detail="Angle must be 90, 180, or 270.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"rot_input_{task_id}.pdf")
    output_filename = f"rotated_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    with open(input_path, "wb") as f:
        f.write(data)

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        writer = PdfWriter()
        selected = set()
        if pages:
            for p in pages.split(","):
                p = p.strip()
                if p.isdigit():
                    idx = int(p) - 1
                    if 0 <= idx < total_pages:
                        selected.add(idx)
        if not selected:
            selected = set(range(total_pages))
        for i, page in enumerate(reader.pages):
            if i in selected:
                page.rotate(angle)
            writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rotation failed: {str(e)}")
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass

    return {
        "message": f"Rotation by {angle}° successful",
        "download_url": f"/download/{output_filename}",
    }


# ─────────────────────── DELETE PAGES ─────────────────────────

@app.post("/delete-pages/")
async def delete_pages(file: UploadFile = File(...), pages: str = Form(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"del_input_{task_id}.pdf")
    output_filename = f"deleted_pages_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    with open(input_path, "wb") as f:
        f.write(data)

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        to_delete = set()
        for p in pages.split(","):
            p = p.strip()
            if p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < total_pages:
                    to_delete.add(idx)
        if not to_delete:
            raise HTTPException(status_code=400, detail="No valid page numbers provided.")
        if len(to_delete) >= total_pages:
            raise HTTPException(status_code=400, detail="Cannot delete all pages.")
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if i not in to_delete:
                writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page deletion failed: {str(e)}")
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass

    return {
        "message": f"Deleted {len(to_delete)} page(s) successfully",
        "download_url": f"/download/{output_filename}",
    }


# ─────────────────────── REORDER PAGES ────────────────────────

@app.post("/reorder-pages/")
async def reorder_pages(file: UploadFile = File(...), order: str = Form(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"reorder_input_{task_id}.pdf")
    output_filename = f"reordered_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    with open(input_path, "wb") as f:
        f.write(data)

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        new_order = []
        for p in order.split(","):
            p = p.strip()
            if p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < total_pages:
                    new_order.append(idx)
        if not new_order:
            raise HTTPException(status_code=400, detail="No valid page order provided.")
        writer = PdfWriter()
        for idx in new_order:
            writer.add_page(reader.pages[idx])
        with open(output_path, "wb") as f:
            writer.write(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reorder failed: {str(e)}")
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass

    return {
        "message": "Pages reordered successfully",
        "download_url": f"/download/{output_filename}",
    }


# ─────────────────────── EXTRACT TEXT ─────────────────────────

@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"txt_input_{task_id}.pdf")
    output_filename = f"text_{task_id}.txt"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    with open(input_path, "wb") as f:
        f.write(data)

    full_text = ""
    try:
        doc = fitz.open(input_path)
        parts = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                parts.append(f"--- Page {i + 1} ---\n{text}")
        doc.close()
        full_text = "\n\n".join(parts)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")
    finally:
        try:
            os.remove(input_path)
        except Exception:
            pass

    preview = full_text[:500] + "..." if len(full_text) > 500 else full_text
    return {
        "message": "Text extracted successfully",
        "download_url": f"/download/{output_filename}",
        "preview": preview,
    }


# ─────────────────────── DOWNLOAD ─────────────────────────────

@app.get("/download/{filename}")
async def download_file(filename: str):
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=safe_filename)


# ─────────────────────── FRONTEND STATIC FILES ────────────────
_frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web', 'out')
if os.path.exists(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
