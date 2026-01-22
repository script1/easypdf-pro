import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { CheckCircle, Circle, Check } from 'lucide-react';

// Set worker source
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PageSelectorProps {
    file: File;
    selectedPages: number[];
    onSelectionChange: (pages: number[]) => void;
}

export function PageSelector({ file, selectedPages, onSelectionChange }: PageSelectorProps) {
    const [numPages, setNumPages] = useState<number>(0);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
        // Requirement: User selects what they want. Default is NONE.
        // So we don't automatically select anything here.
    }

    const togglePage = (pageIndex: number) => {
        if (selectedPages.includes(pageIndex)) {
            onSelectionChange(selectedPages.filter(p => p !== pageIndex));
        } else {
            onSelectionChange([...selectedPages, pageIndex].sort((a, b) => a - b));
        }
    };

    const selectAll = () => {
        onSelectionChange(Array.from({ length: numPages }, (_, i) => i));
    }

    const deselectAll = () => {
        onSelectionChange([]);
    }

    return (
        <div className="w-full flex flex-col gap-4">
            <div className="flex justify-between items-center bg-white/50 p-3 rounded-xl border border-white/60 backdrop-blur-sm shadow-sm">
                <span className="font-semibold text-slate-700">{selectedPages.length} pages selected</span>
                <div className="flex gap-2">
                    <button onClick={selectAll} className="text-xs font-bold text-blue-600 hover:text-blue-700 px-4 py-2 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors">Select All</button>
                    <button onClick={deselectAll} className="text-xs font-bold text-slate-600 hover:text-slate-800 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors">Clear</button>
                </div>
            </div>

            <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3 max-h-[500px] overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-blue-200 scrollbar-track-transparent">
                <Document
                    file={file}
                    onLoadSuccess={onDocumentLoadSuccess}
                    loading={<div className="col-span-full flex flex-col items-center justify-center py-12 text-slate-400 font-medium">Loading Document...</div>}
                    className="contents"
                >
                    {Array.from(new Array(numPages), (el, index) => {
                        const isSelected = selectedPages.includes(index);
                        return (
                            <div
                                key={`page_${index + 1}`}
                                onClick={() => togglePage(index)}
                                className={`relative group cursor-pointer transition-all duration-200 rounded-lg overflow-hidden border-2 
                                ${isSelected ? 'border-blue-500 ring-2 ring-blue-200 shadow-lg transform scale-95' : 'border-slate-200 hover:border-blue-300 hover:shadow-md'}`}
                            >
                                {/* Overlay for selected state */}
                                {isSelected && (
                                    <div className="absolute inset-0 z-10 bg-blue-500/20 backdrop-blur-[1px] flex items-center justify-center transition-all">
                                        <div className="bg-blue-500 p-1.5 rounded-full shadow-lg transform scale-100 animate-in zoom-in">
                                            <Check className="w-5 h-5 text-white stroke-[3px]" />
                                        </div>
                                    </div>
                                )}

                                <div className="bg-slate-100 min-h-[100px] relative pointer-events-none flex items-center justify-center">
                                    <Page
                                        pageNumber={index + 1}
                                        width={100}
                                        renderTextLayer={false}
                                        renderAnnotationLayer={false}
                                        className="shadow-sm"
                                    />
                                </div>

                                <div className={`absolute bottom-0 w-full text-center text-[10px] font-bold py-1 border-t transition-colors
                                ${isSelected ? 'bg-blue-500 text-white border-blue-500' : 'bg-white/90 text-slate-500 border-slate-100'}`}>
                                    Page {index + 1}
                                </div>
                            </div>
                        );
                    })}
                </Document>
            </div>
        </div>
    );
}
