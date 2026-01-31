"use client";

import React, { useState, useRef, useEffect } from "react";
import { FileVerifier } from "@/components/verification/FileVerifier";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ShieldCheck, X, Check, Info } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

const API_URL = "/api/v1";

export default function VerifyPage() {
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<any>(null);
  const pieChartRef = useRef<HTMLCanvasElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const verifyFiles = async (document: File, humansign: File) => {
    setIsVerifying(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("document", document);
      formData.append("humansign", humansign);

      const response = await fetch(`${API_URL}/verify-files`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Verification failed");

      const mapped = {
        status: data.verification_result,
        confidence: data.confidence_score,
        details: data.details,
      };
      setResult(mapped);
      // Scroll to results after a short delay to allow rendering
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }, 300);
    } catch (error) {
      console.error(error);
      alert("Verification failed: " + (error as Error).message);
    } finally {
      setIsVerifying(false);
    }
  };

  // Draw pie chart for content analysis when result is available
  useEffect(() => {
    if (
      !pieChartRef.current ||
      !result?.details?.content_analysis
    )
      return;

    const canvas = pieChartRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const analysis = result.details.content_analysis;
    const typed = analysis.typed_percentage || 0;
    const pasted = analysis.pasted_percentage || 0;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const size = 200;
    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size / 2 - 10;

    let currentAngle = -Math.PI / 2;

    if (typed > 0) {
      const sliceAngle = (typed / 100) * 2 * Math.PI;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(
        centerX,
        centerY,
        radius,
        currentAngle,
        currentAngle + sliceAngle,
      );
      ctx.closePath();
      ctx.fillStyle = "#10b981";
      ctx.fill();
      currentAngle += sliceAngle;
    }

    if (pasted > 0) {
      const sliceAngle = (pasted / 100) * 2 * Math.PI;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(
        centerX,
        centerY,
        radius,
        currentAngle,
        currentAngle + sliceAngle,
      );
      ctx.closePath();
      ctx.fillStyle = "#f59e0b";
      ctx.fill();
    }

    // Donut hole
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.6, 0, 2 * Math.PI);
    ctx.fillStyle = "#ffffff";
    ctx.fill();

    // Center text
    ctx.fillStyle = "#1f1f1f";
    ctx.font = "bold 24px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`${typed}%`, centerX, centerY - 8);
    ctx.font = "12px Inter, sans-serif";
    ctx.fillStyle = "#666";
    ctx.fillText("Typed", centerX, centerY + 12);
  }, [result]);

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
          className="w-full max-w-4xl"
        >
          {!result && (
            <div className="text-center mb-10">
              <h2 className="text-4xl font-extrabold tracking-tight mb-3">
                Verify Authenticity
              </h2>
              <p className="text-muted-foreground text-lg">
                Upload the original document and its corresponding Humansign
                signature file to cryptographically verify its integrity and
                origin.
              </p>
            </div>
          )}

          <div className={result ? "mt-4" : ""}>
            <FileVerifier
              onVerify={verifyFiles}
              isVerifying={isVerifying}
              onReset={() => setResult(null)}
              result={result}
            />
          </div>

          {/* Inline Verification Results - Display below FileVerifier */}
          {result && (
            <motion.div
              ref={resultsRef}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mt-10 bg-white rounded-2xl shadow-xl border border-border/40 p-8 scroll-mt-10"
            >
              <h3 className="text-3xl font-bold text-gray-800 mb-8 pb-4 border-b border-gray-200">
                Verification Results
              </h3>

              <div className="space-y-8">
                {/* Verification Status */}
                <div
                  className={
                    "p-6 rounded-xl border-2 " +
                    (result.status === "GENUINE"
                      ? "bg-green-50 border-green-200"
                      : "bg-red-50 border-red-200")
                  }
                >
                  <div className="flex items-center gap-4 mb-3">
                    {result.status === "GENUINE" ? (
                      <Check className="w-8 h-8 text-green-600" />
                    ) : (
                      <X className="w-8 h-8 text-red-600" />
                    )}
                    <span
                      className={
                        "font-bold text-3xl " +
                        (result.status === "GENUINE"
                          ? "text-green-700"
                          : "text-red-700")
                      }
                    >
                      {result.status}
                    </span>
                  </div>
                  <p className="text-base text-gray-600 ml-12">
                    Confidence: {(result.confidence * 100).toFixed(2)}%
                  </p>
                </div>

                {/* Content Analysis */}
                {result.details?.content_analysis && (
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 p-8 rounded-xl border border-gray-200">
                    <h4 className="font-bold text-xl text-gray-800 mb-6">
                      Content Analysis
                    </h4>

                    {/* Check if content analysis has data */}
                    {result.details.content_analysis.total_chars > 0 ? (
                      <>
                        {/* Pie Chart */}
                        <div className="flex justify-center mb-8">
                          <div className="relative">
                            <canvas
                              ref={pieChartRef}
                              width={200}
                              height={200}
                              className="drop-shadow-lg"
                            />
                            <div className="flex justify-center gap-8 mt-5">
                              <div className="flex items-center gap-2">
                                <div className="w-4 h-4 rounded-full bg-green-500"></div>
                                <span className="text-sm font-medium text-gray-700">
                                  Typed
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="w-4 h-4 rounded-full bg-orange-500"></div>
                                <span className="text-sm font-medium text-gray-700">
                                  Pasted
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-5">
                          <div>
                            <div className="flex justify-between text-base mb-2">
                              <span className="font-semibold text-gray-700">
                                Typed Content
                              </span>
                              <span className="font-bold text-green-600 text-lg">
                                {result.details.content_analysis.typed_percentage}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-4">
                              <div
                                className="bg-green-500 h-4 rounded-full transition-all duration-500"
                                style={{
                                  width: `${result.details.content_analysis.typed_percentage}%`,
                                }}
                              />
                            </div>
                            <p className="text-sm text-gray-500 mt-2">
                              {result.details.content_analysis.typed_chars}{" "}
                              characters
                            </p>
                          </div>

                          <div>
                            <div className="flex justify-between text-base mb-2">
                              <span className="font-semibold text-gray-700">
                                Pasted Content
                              </span>
                              <span className="font-bold text-orange-600 text-lg">
                                {result.details.content_analysis.pasted_percentage}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-4">
                              <div
                                className="bg-orange-500 h-4 rounded-full transition-all duration-500"
                                style={{
                                  width: `${result.details.content_analysis.pasted_percentage}%`,
                                }}
                              />
                            </div>
                            <p className="text-sm text-gray-500 mt-2">
                              {result.details.content_analysis.pasted_chars}{" "}
                              characters
                            </p>
                          </div>

                          <div className="pt-5 border-t border-gray-300">
                            <div className="flex justify-between items-center">
                              <span className="font-semibold text-gray-700 text-lg">
                                Authenticity Score
                              </span>
                              <span className="font-bold text-2xl text-blue-600">
                                {result.details.content_analysis.authenticity_score}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                        <div className="flex justify-center mb-3">
                          <Info className="w-12 h-12 text-yellow-600" />
                        </div>
                        <h5 className="font-semibold text-gray-800 mb-2">
                          Content Analysis Not Available
                        </h5>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          This document was created with an older version of
                          HumanSign that didn't track typed vs. pasted content.
                          <br />
                          To see content analysis, please create a new document
                          using the latest version.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Keystroke Stats */}
                <div className="bg-gradient-to-br from-blue-50 to-blue-100/50 p-8 rounded-xl border border-blue-200">
                  <h4 className="font-bold text-xl text-gray-800 mb-6">
                    Keystroke Analysis
                  </h4>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-white/80 p-6 rounded-lg shadow-sm">
                      <p className="text-sm text-gray-600 mb-2 font-medium">
                        Events Captured
                      </p>
                      <p className="font-bold text-3xl text-gray-800">
                        {result.details?.keystroke_count || 0}
                      </p>
                    </div>
                    <div className="bg-white/80 p-6 rounded-lg shadow-sm">
                      <p className="text-sm text-gray-600 mb-2 font-medium">
                        Features Extracted
                      </p>
                      <p className="font-bold text-3xl text-gray-800">
                        {result.details?.features_extracted || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
