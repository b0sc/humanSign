"use client"

import React, { useState } from 'react';
import { FileVerifier } from "@/components/verification/FileVerifier";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

const API_URL = "/api/v1";

export default function VerifyPage() {
    const [isVerifying, setIsVerifying] = useState(false);
    const [result, setResult] = useState<any>(null);

    const verifyFiles = async (document: File, humansign: File) => {
        setIsVerifying(true);
        setResult(null);
        try {
            const formData = new FormData();
            formData.append("document", document);
            formData.append("humansign", humansign);

            const response = await fetch(`${API_URL}/verify-files`, {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Verification failed");

            setResult({
                status: data.verification_result,
                confidence: data.confidence_score,
                details: data.details
            });
        } catch (error) {
            console.error(error);
            alert("Verification failed: " + (error as Error).message);
        } finally {
            setIsVerifying(false);
        }
    };

    return (
        <div className="min-h-screen bg-muted/20 font-sans">
            {/* Header */}
            <header className="bg-background border-b border-border/40 px-6 py-4 flex items-center justify-between sticky top-0 z-50">
                <div className="flex items-center gap-4">
                    <Link href="/" passHref>
                        <Button variant="ghost" size="icon" className="rounded-full">
                            <ArrowLeft className="w-5 h-5" />
                        </Button>
                    </Link>
                    <div className="flex items-center gap-2">
                        <ShieldCheck className="w-6 h-6 text-primary" />
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
                            Document Verification
                        </h1>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-12 flex flex-col items-center">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-2xl"
                >
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-extrabold tracking-tight mb-2">Verify Authenticity</h2>
                        <p className="text-muted-foreground">
                            Upload the original document and its corresponding Humansign signature file to cryptographically verify its integrity and origin.
                        </p>
                    </div>

                    <FileVerifier
                        onVerify={verifyFiles}
                        isVerifying={isVerifying}
                        result={result}
                    />
                </motion.div>
            </main>
        </div>
    );
}
