import React, { useRef, useState } from 'react';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';

interface FileUploaderProps {
    onFileSelect?: (file: File | null) => void;
    onFilesSelect?: (files: File[]) => void;
    accept?: string;
    multiple?: boolean;
}

export function FileUploader({ onFileSelect, onFilesSelect, accept = ".pdf", multiple = false }: FileUploaderProps) {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
        else if (e.type === "dragleave") setDragActive(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (!e.dataTransfer.files || e.dataTransfer.files.length === 0) return;
        if (multiple) handleMultipleFiles(Array.from(e.dataTransfer.files));
        else handleSingleFile(e.dataTransfer.files[0]);
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (!e.target.files || e.target.files.length === 0) return;
        if (multiple) handleMultipleFiles(Array.from(e.target.files));
        else handleSingleFile(e.target.files[0]);
    };

    const handleSingleFile = (file: File) => {
        if (accept === ".pdf" && file.type !== "application/pdf") {
            alert("Please upload a PDF file");
            return;
        }
        setSelectedFile(file);
        onFileSelect?.(file);
    };

    const handleMultipleFiles = (files: File[]) => {
        const valid = accept === ".pdf" ? files.filter(f => f.type === "application/pdf") : files;
        if (valid.length === 0) {
            alert(accept === ".pdf" ? "Please upload PDF files" : "No valid files selected");
            return;
        }
        setSelectedFiles(valid);
        onFilesSelect?.(valid);
    };

    const clearSingle = () => {
        setSelectedFile(null);
        onFileSelect?.(null);
        if (inputRef.current) inputRef.current.value = "";
    };

    const removeFile = (index: number) => {
        const updated = selectedFiles.filter((_, i) => i !== index);
        setSelectedFiles(updated);
        onFilesSelect?.(updated);
        if (inputRef.current) inputRef.current.value = "";
    };

    if (multiple && selectedFiles.length > 0) {
        return (
            <div className="w-full space-y-3">
                <div className="p-4 bg-blue-50 border-2 border-dashed border-blue-200 rounded-xl">
                    <p className="font-semibold text-slate-700 mb-3">{selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected</p>
                    <div className="flex flex-col gap-2">
                        {selectedFiles.map((f, i) => (
                            <div key={i} className="flex items-center justify-between bg-white rounded-lg px-4 py-2 border border-slate-200 shadow-sm">
                                <div className="flex items-center gap-3">
                                    <FileIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />
                                    <div>
                                        <p className="font-medium text-slate-700 text-sm">{f.name}</p>
                                        <p className="text-xs text-slate-400">{(f.size / 1024 / 1024).toFixed(2)} MB</p>
                                    </div>
                                </div>
                                <button onClick={() => removeFile(i)} className="p-1 hover:bg-red-50 rounded-full transition-colors text-slate-400 hover:text-red-500">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
                <button onClick={() => inputRef.current?.click()}
                    className="w-full py-2 border border-dashed border-slate-300 rounded-xl text-sm text-slate-500 hover:border-blue-400 hover:text-blue-500 transition-colors">
                    + Add more files
                </button>
                <input ref={inputRef} type="file" className="hidden" accept={accept} multiple onChange={handleChange} />
            </div>
        );
    }

    if (!multiple && selectedFile) {
        return (
            <div className="w-full p-6 bg-blue-50 border-2 border-dashed border-blue-200 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-white rounded-lg shadow-sm">
                        <FileIcon className="w-8 h-8 text-blue-500" />
                    </div>
                    <div>
                        <p className="font-semibold text-slate-700">{selectedFile.name}</p>
                        <p className="text-sm text-slate-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                </div>
                <button onClick={clearSingle} className="p-2 hover:bg-white rounded-full transition-colors text-slate-400 hover:text-red-500">
                    <X className="w-5 h-5" />
                </button>
            </div>
        );
    }

    return (
        <div
            className={`relative w-full h-64 border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-all cursor-pointer bg-white/50 backdrop-blur-sm ${
                dragActive ? "border-blue-500 bg-blue-50/50" : "border-slate-300 hover:border-blue-400 hover:bg-slate-50/50"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
        >
            <input ref={inputRef} type="file" className="hidden" accept={accept} multiple={multiple} onChange={handleChange} />
            <div className="p-4 bg-white rounded-full shadow-sm mb-4">
                <UploadCloud className={`w-8 h-8 ${dragActive ? "text-blue-600" : "text-blue-500"}`} />
            </div>
            <p className="text-lg font-medium text-slate-700 mb-1">
                {multiple ? 'Click to upload files or drag and drop' : 'Click to upload or drag and drop'}
            </p>
            <p className="text-sm text-slate-400">
                {accept === 'image/*' ? 'Images (JPG, PNG, WEBP) — max 50MB each' : 'PDF files only — max 50MB'}
            </p>
        </div>
    );
}
