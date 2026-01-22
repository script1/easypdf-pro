import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { ArrowLeft, Lock, Scissors, Image as ImageIcon, Zap, FileText, Layers } from 'lucide-react';

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

export function ToolConfig({ toolName, files, onBack, onProcess, isProcessing }: ToolConfigProps) {
    const [password, setPassword] = useState('');
    const [selectedPages, setSelectedPages] = useState<number[]>([]);

    const handleProcess = () => {
        // Validate
        if (toolName === 'Protect PDF' && !password) {
            alert("Please enter a password");
            return;
        }
        if ((toolName === 'Split PDF' || toolName === 'PDF to JPG') && selectedPages.length === 0) {
            alert("Please select at least one page");
            return;
        }

        onProcess({
            password,
            selectedPages
        });
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

                {/* File Info */}
                <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg">
                    <p className="font-semibold text-slate-700 mb-1">selected File(s):</p>
                    <div className="flex flex-wrap gap-2">
                        {files.map((f, i) => (
                            <span key={i} className="px-3 py-1 bg-white rounded-md text-sm text-slate-600 border border-slate-200">
                                {f.name}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Protect PDF Config */}
                {toolName === 'Protect PDF' && (
                    <div className="flex flex-col gap-2 max-w-md">
                        <label className="font-medium text-slate-700">Set Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <input
                                type="password"
                                className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="Enter secure password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                        <p className="text-sm text-slate-500">This password will be required to open the file.</p>
                    </div>
                )}

                {/* Page Selection (Split / JPG) */}
                {(toolName === 'Split PDF' || toolName === 'PDF to JPG') && files.length === 1 && (
                    <div className="flex flex-col gap-2">
                        <label className="font-medium text-slate-700 mb-2">Select Pages to Extract</label>
                        <PageSelector
                            file={files[0]}
                            selectedPages={selectedPages}
                            onSelectionChange={setSelectedPages}
                        />
                    </div>
                )}

                {/* Merge / Convert (Simple tools) */}
                {(toolName === 'Merge PDF' || toolName === 'PDF to Word' || toolName === 'Compress') && (
                    <div className="text-slate-600 bg-slate-50 p-6 rounded-lg text-center">
                        <p>Ready to process! No additional configuration needed.</p>
                    </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-end pt-6 border-t border-slate-200 mt-4">
                    <button
                        onClick={handleProcess}
                        disabled={isProcessing}
                        className="flex items-center gap-2 px-8 py-3 bg-blue-600 text-white rounded-xl font-bold shadow-lg hover:shadow-blue-500/40 hover:-translate-y-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isProcessing ? (
                            <>Processing...</>
                        ) : (
                            <>
                                Start Processing <Zap className="w-5 h-5 fill-current" />
                            </>
                        )}
                    </button>
                </div>

            </div>
        </div>
    );
}
