import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { ArrowLeft, Lock, Zap, Unlock, Droplets, Trash2, ArrowUpDown } from 'lucide-react';

const PageSelector = dynamic(() => import('./PageSelector').then(mod => mod.PageSelector), {
    ssr: false,
    loading: () => <div className="w-full h-48 flex items-center justify-center text-slate-400">Loading PDF Preview...</div>
});

interface ToolConfigProps {
    toolName: string;
    files: File[];
    onBack: () => void;
    onProcess: (config: any) => void;
    isProcessing: boolean;
}

const SIMPLE_TOOLS = ['PDF to Word', 'Merge PDF', 'Compress', 'Images to PDF', 'Extract Text'];

export function ToolConfig({ toolName, files, onBack, onProcess, isProcessing }: ToolConfigProps) {
    const [password, setPassword] = useState('');
    const [selectedPages, setSelectedPages] = useState<number[]>([]);
    const [watermarkText, setWatermarkText] = useState('');
    const [angle, setAngle] = useState('90');
    const [pageOrder, setPageOrder] = useState('');

    const handleProcess = () => {
        if ((toolName === 'Protect PDF' || toolName === 'Unlock PDF') && !password) {
            alert("Please enter a password");
            return;
        }
        if ((toolName === 'Split PDF' || toolName === 'PDF to JPG') && selectedPages.length === 0) {
            alert("Please select at least one page");
            return;
        }
        if (toolName === 'Delete Pages' && selectedPages.length === 0) {
            alert("Please select at least one page to delete");
            return;
        }
        if (toolName === 'Reorder Pages' && !pageOrder.trim()) {
            alert("Please enter the new page order");
            return;
        }
        if (toolName === 'Watermark' && !watermarkText.trim()) {
            alert("Please enter watermark text");
            return;
        }
        onProcess({ password, selectedPages, watermarkText, angle, pageOrder });
    };

    return (
        <div className="w-full max-w-4xl bg-white/70 backdrop-blur-lg rounded-2xl shadow-xl p-8 border border-white/50 animate-in fade-in slide-in-from-bottom-4">
            <div className="flex items-center gap-4 mb-8">
                <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                    <ArrowLeft className="w-6 h-6 text-slate-600" />
                </button>
                <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    Configure: <span className="text-blue-600">{toolName}</span>
                </h2>
            </div>

            <div className="flex flex-col gap-6">

                <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg">
                    <p className="font-semibold text-slate-700 mb-1">Selected File{files.length > 1 ? 's' : ''}:</p>
                    <div className="flex flex-wrap gap-2">
                        {files.map((f, i) => (
                            <span key={i} className="px-3 py-1 bg-white rounded-md text-sm text-slate-600 border border-slate-200">
                                {f.name}
                            </span>
                        ))}
                    </div>
                </div>

                {toolName === 'Protect PDF' && (
                    <div className="flex flex-col gap-2 max-w-md">
                        <label className="font-medium text-slate-700">Set Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input type="password" className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="Enter secure password" value={password} onChange={(e) => setPassword(e.target.value)} />
                        </div>
                        <p className="text-sm text-slate-500">This password will be required to open the PDF.</p>
                    </div>
                )}

                {toolName === 'Unlock PDF' && (
                    <div className="flex flex-col gap-2 max-w-md">
                        <label className="font-medium text-slate-700">Current Password</label>
                        <div className="relative">
                            <Unlock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input type="password" className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none"
                                placeholder="Enter current PDF password" value={password} onChange={(e) => setPassword(e.target.value)} />
                        </div>
                        <p className="text-sm text-slate-500">Enter the password used to protect this PDF.</p>
                    </div>
                )}

                {toolName === 'Watermark' && (
                    <div className="flex flex-col gap-2 max-w-md">
                        <label className="font-medium text-slate-700">Watermark Text</label>
                        <div className="relative">
                            <Droplets className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input type="text" className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-cyan-500 outline-none"
                                placeholder="e.g. CONFIDENTIAL" value={watermarkText} onChange={(e) => setWatermarkText(e.target.value)} />
                        </div>
                        <p className="text-sm text-slate-500">This text will appear as a diagonal watermark on all pages.</p>
                    </div>
                )}

                {toolName === 'Rotate PDF' && (
                    <div className="flex flex-col gap-2 max-w-xs">
                        <label className="font-medium text-slate-700">Rotation Angle</label>
                        <div className="flex gap-3">
                            {['90', '180', '270'].map(a => (
                                <button key={a} onClick={() => setAngle(a)}
                                    className={`flex-1 py-3 rounded-lg font-bold border-2 transition-all ${
                                        angle === a ? 'border-orange-500 bg-orange-50 text-orange-600' : 'border-slate-200 bg-white text-slate-600 hover:border-orange-300'
                                    }`}>
                                    {a}°
                                </button>
                            ))}
                        </div>
                        <p className="text-sm text-slate-500">Clockwise rotation applied to all pages.</p>
                    </div>
                )}

                {toolName === 'Delete Pages' && files.length === 1 && (
                    <div className="flex flex-col gap-2">
                        <label className="font-medium text-slate-700 mb-2 flex items-center gap-2">
                            <Trash2 className="w-4 h-4 text-red-500" /> Select Pages to Delete
                        </label>
                        <PageSelector file={files[0]} selectedPages={selectedPages} onSelectionChange={setSelectedPages} />
                        {selectedPages.length > 0 && (
                            <p className="text-sm text-red-500 mt-1">{selectedPages.length} page{selectedPages.length > 1 ? 's' : ''} will be permanently deleted.</p>
                        )}
                    </div>
                )}

                {toolName === 'Reorder Pages' && (
                    <div className="flex flex-col gap-2 max-w-md">
                        <label className="font-medium text-slate-700 flex items-center gap-2">
                            <ArrowUpDown className="w-4 h-4 text-violet-500" /> New Page Order
                        </label>
                        <input type="text" className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none"
                            placeholder="e.g. 3,1,2 or 1,3,2,4" value={pageOrder} onChange={(e) => setPageOrder(e.target.value)} />
                        <p className="text-sm text-slate-500">
                            Enter comma-separated page numbers in the order you want them. Example: <code className="bg-slate-100 px-1 rounded">3,1,2</code> puts page 3 first.
                        </p>
                    </div>
                )}

                {(toolName === 'Split PDF' || toolName === 'PDF to JPG') && files.length === 1 && (
                    <div className="flex flex-col gap-2">
                        <label className="font-medium text-slate-700 mb-2">Select Pages to Extract</label>
                        <PageSelector file={files[0]} selectedPages={selectedPages} onSelectionChange={setSelectedPages} />
                    </div>
                )}

                {SIMPLE_TOOLS.includes(toolName) && (
                    <div className="text-slate-600 bg-slate-50 p-6 rounded-lg text-center">
                        <p>Ready to process! No additional configuration needed.</p>
                    </div>
                )}

                <div className="flex justify-end pt-6 border-t border-slate-200 mt-4">
                    <button onClick={handleProcess} disabled={isProcessing}
                        className="flex items-center gap-2 px-8 py-3 bg-blue-600 text-white rounded-xl font-bold shadow-lg hover:shadow-blue-500/40 hover:-translate-y-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                        {isProcessing ? (
                            <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Processing...</>
                        ) : (
                            <>Start Processing <Zap className="w-5 h-5 fill-current" /></>
                        )}
                    </button>
                </div>

            </div>
        </div>
    );
}
