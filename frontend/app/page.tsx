"use client"

import React from 'react';
import { ShieldCheck, ArrowRight, Layers, FilePlus } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans overflow-hidden relative selection:bg-primary/20">
      {/* Premium Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-[120px]" />
        <div className="absolute top-[40%] left-[40%] w-[300px] h-[300px] bg-purple-500/5 rounded-full blur-[100px] animate-pulse duration-1000" />
      </div>

      <header className="px-8 lg:px-12 py-8 flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/10 text-primary border border-primary/20 rounded-xl flex items-center justify-center shadow-lg shadow-primary/5 backdrop-blur-md">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/80">HumanSign</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground/80">
          <span className="hover:text-foreground cursor-pointer transition-colors duration-300">Enterprise</span>
          <span className="hover:text-foreground cursor-pointer transition-colors duration-300">Security</span>
          <span className="hover:text-foreground cursor-pointer transition-colors duration-300">Developers</span>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 relative z-10 w-full max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center mb-20 max-w-4xl"
        >
          <h1 className="text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1] mb-8">
            Verify Digital <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-blue-600">Humanity.</span>
          </h1>
          <p className="text-xl text-muted-foreground/80 leading-relaxed max-w-2xl mx-auto font-light">
            The new standard for provenance. Create documents with biometric keystroke analysis or cryptographically validate existing files.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-5xl px-4 lg:px-8">
          {/* Create Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Link href="/editor" className="group block h-full">
              <div className="h-full p-10 rounded-[2rem] bg-card/30 backdrop-blur-xl border border-white/10 dark:border-white/5 shadow-2xl shadow-black/5 hover:shadow-primary/10 hover:border-primary/20 transition-all duration-500 relative overflow-hidden flex flex-col items-start text-left group-hover:-translate-y-1">
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                <div className="mb-8 w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300 relative z-10">
                  <FilePlus className="w-6 h-6" />
                </div>

                <h3 className="text-2xl font-bold mb-4 z-10">Create Document</h3>
                <p className="text-muted-foreground mb-8 leading-relaxed font-light z-10">
                  Draft secure documents in our intelligent editor. We analyze unique typing dynamics to embed biometric proof of authorship.
                </p>

                <div className="mt-auto flex items-center text-sm font-semibold text-primary group-hover:translate-x-1 transition-transform z-10">
                  Open Editor <ArrowRight className="ml-2 w-4 h-4" />
                </div>
              </div>
            </Link>
          </motion.div>

          {/* Validate Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Link href="/verify" className="group block h-full">
              <div className="h-full p-10 rounded-[2rem] bg-card/30 backdrop-blur-xl border border-white/10 dark:border-white/5 shadow-2xl shadow-black/5 hover:shadow-emerald-500/10 hover:border-emerald-500/20 transition-all duration-500 relative overflow-hidden flex flex-col items-start text-left group-hover:-translate-y-1">
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                <div className="mb-8 w-14 h-14 bg-emerald-500/10 text-emerald-600 rounded-2xl flex items-center justify-center group-hover:bg-emerald-500 group-hover:text-white transition-all duration-300 relative z-10">
                  <Layers className="w-6 h-6" />
                </div>

                <h3 className="text-2xl font-bold mb-4 z-10">Validate Documents</h3>
                <p className="text-muted-foreground mb-8 leading-relaxed font-light z-10">
                  Received a signed file? Upload the original document and signature to cryptographically verify its integrity and origin.
                </p>

                <div className="mt-auto flex items-center text-sm font-semibold text-emerald-500 group-hover:translate-x-1 transition-transform z-10">
                  Start Verification <ArrowRight className="ml-2 w-4 h-4" />
                </div>
              </div>
            </Link>
          </motion.div>
        </div>
      </main>

      <footer className="py-8 text-center text-xs font-medium text-muted-foreground/40 tracking-wide uppercase relative z-10">
        © {new Date().getFullYear()} HumanSign. Built for security & transparency.
      </footer>
    </div>
  );
}
