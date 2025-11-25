// src/PythonProjectsPage.js
import React from "react";
import "./App.css";
import { Link } from "react-router-dom";

export default function PythonProjectsPage() {
    return (
        <div className="container">
            <Link to="/" className="back-btn">
                ← Back
            </Link>

            <header>
                <h1>Python Projects (Preview)</h1>
                <p className="subtitle">
                    A focused view of Python-heavy repositories in Seattle&apos;s open source ecosystem.
                </p>
            </header>

            <div className="info-panel">
                <p>
                    This page will surface projects that lean heavily on Python for data science,
                    machine learning, backend APIs, and developer tooling.
                </p>
                <p>
                    The design and ranking logic will reuse the same SSR infrastructure, with
                    additional filters for stack type, domain, and project maturity.
                </p>
                <p style={{ opacity: 0.8 }}>
                    Coming soon — for now, please explore the main{" "}
                    <a href="/rankings" className="inline-link">
                        Seattle Source Ranker rankings
                    </a>.
                </p>
            </div>
        </div>
    );
}
