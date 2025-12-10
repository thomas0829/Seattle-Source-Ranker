import React, { useEffect, useRef, useState } from "react";
import "./App.css";
import { Link } from "react-router-dom";

export default function ValidationPage() {
    const hasRestoredRef = useRef(false);
    // State to track which section is active: 'method' (original) or 'results' (new summary)
    const [activeSection, setActiveSection] = useState('method');

    // --- SCROLL MANAGEMENT (Keeping the original logic) ---
    // Save scroll position before unload (for F5 refresh)
    useEffect(() => {
        const handleBeforeUnload = () => {
            sessionStorage.setItem('validationScrollPosition', window.pageYOffset.toString());
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, []);

    // Restore scroll position after mount (only if coming from F5 refresh)
    useEffect(() => {
        const savedScrollPosition = sessionStorage.getItem('validationScrollPosition');
        if (savedScrollPosition && !hasRestoredRef.current) {
            hasRestoredRef.current = true;
            setTimeout(() => {
                window.scrollTo({ top: parseInt(savedScrollPosition, 10), behavior: 'smooth' });
                sessionStorage.removeItem('validationScrollPosition');
            }, 100);
        } else if (!savedScrollPosition) {
            // First time entering page - scroll to top
            window.scrollTo(0, 0);
        }
    }, []);
    // --- END SCROLL MANAGEMENT ---

    // Define consistent styles for the tab buttons
    const getButtonStyle = (sectionKey) => ({
        padding: '10px 20px',
        margin: '0 5px',
        cursor: 'pointer',
        borderRadius: '8px',
        fontSize: '1rem',
        fontWeight: 600,
        transition: 'background-color 0.2s, color 0.2s',
        border: '1px solid',
        // Active state
        backgroundColor: activeSection === sectionKey ? '#7dd3fc' : 'transparent',
        color: activeSection === sectionKey ? '#0f172a' : 'rgba(255,255,255,0.85)',
        borderColor: activeSection === sectionKey ? '#7dd3fc' : 'rgba(255,255,255,0.15)',
    });

    // Base style for the content container
    const contentContainerStyle = {
        background: "rgba(255,255,255,0.05)",
        padding: "25px 30px",
        borderRadius: "15px",
        backdropFilter: "blur(15px)",
        border: "1px solid rgba(255,255,255,0.08)",
        color: "rgba(255,255,255,0.85)",
        lineHeight: "1.7",
        marginTop: "20px",
    };

    // Helper component for the original (Methods) content - UPDATED
    const ValidationMethodsContent = () => (
        <>
            <h2 style={{ color: "#7dd3fc", marginBottom: "10px" }}>Validation Overview</h2>
            <p>
                Seattle-Source-Ranker provides a complete validation pipeline ensuring that all GitHub project data and ranking outputs are <strong>structurally correct</strong>, <strong>statistically clean</strong>, and <strong>ready for downstream analysis or frontend display</strong>.
            </p>
            <p>
                This repository does <strong>not</strong> simply compute rankings — it enforces a full multi-stage verification workflow, turning raw JSON project data into validated, trustworthy ranking outputs.
            </p>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h2 style={{ color: "#7dd3fc" }}>Validation Workflow</h2>
            <p>The core validation process transforms raw collected data into verified outputs through four distinct stages:</p>

            <pre
                style={{
                    background: "rgba(0,0,0,0.3)",
                    padding: "15px",
                    borderRadius: "10px",
                    marginTop: "15px",
                    overflowX: "auto",
                    color: "#9ecbff",
                    fontSize: "0.9rem",
                    lineHeight: "1.2",
                }}
            >
{`🗂 Raw Input
┌─────────────────────────────┐
│ Raw Project Data            │
│ (seattle_projects.json)     │
└───────────────┬─────────────┘
                ↓
📝 Convert Format
┌─────────────────────────────┐
│ JSON → CSV Conversion       │
│ (json_to_csv.py)            │
└───────────────┬─────────────┘
                ↓
🔍 Metadata Validation
┌─────────────────────────────┐
│ Repo Metrics Validation     │
│ - Consistency Checks        │
│ - Quality Summary           │
│ (validate_repo_metrics.py)  │
└───────────────┬─────────────┘
                ↓
🏆 Ranking Validation
┌─────────────────────────────┐
│ Ranking Validation          │
│ - Overall ranking           │
│ - Python+PyPI ranking       │
│ (validate_rankings.py)      │
└───────────────┬─────────────┘
                ↓
📤 Final Outputs
┌─────────────────────────────┐
│ Validation Outputs          │
│ - overall_ranking_validation│
│ - python_ranking_validation │
│ - repo_metrics_consistency  │
│ - repo_metrics_quality      │
│ - repo_metric_outliers.csv  │
│ (validation_outputs/)       │
└─────────────────────────────┘`}
            </pre>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h2 style={{ color: "#7dd3fc" }}>Ranking Outputs</h2>
            <h3 style={{ color: "#bae6fd" }}>1. Overall Ranking</h3>
            <ul style={{ marginLeft: "20px" }}>
                <li>Top <strong>10,000</strong> GitHub projects scored and globally ranked</li>
                <li>Uses enhanced SSR scoring (stars, forks, maturity, activity, health)</li>
            </ul>

            <h3 style={{ color: "#bae6fd", marginTop: "15px" }}>2. Python + PyPI Ranking</h3>
            <ul style={{ marginLeft: "20px" }}>
                <li>Python repositories only</li>
                <li>Additional bonus for PyPI packages</li>
                <li>Used for Python-specific leaderboard</li>
            </ul>
            <p style={{ marginTop: "10px" }}>
                Paginated outputs are found in:
                <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>frontend/public/pages/all/page_*.json</code> and
                <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>frontend/public/pages/python_pypi/page_*.json</code>
            </p>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h2 style={{ color: "#7dd3fc" }}>Validation Suite</h2>
            <p>
                Validation scripts are located in the dedicated:
                <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>validation/</code> directory.
            </p>

            <h3 style={{ color: "#bae6fd", marginTop: "15px" }}>Validation Summary (High-Visibility Table)</h3>
            <div style={{ overflowX: "auto", marginTop: "10px" }}>
                <table
                    style={{
                        width: "100%",
                        borderCollapse: "collapse",
                        fontSize: "0.9rem",
                    }}
                >
                    <thead>
                    <tr>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>Category</th>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>Purpose</th>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>Findings</th>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>Status</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td style={{ padding: "6px 8px" }}>Overall Ranking</td>
                        <td style={{ padding: "6px 8px" }}>Validate sorting, ranking continuity, duplication</td>
                        <td style={{ padding: "6px 8px" }}>10,000 repos, perfectly sorted, continuous rank, no duplicates</td>
                        <td style={{ padding: "6px 8px", color: "#6ee7b7" }}><strong>🟢 Passed</strong></td>
                    </tr>
                    <tr>
                        <td style={{ padding: "6px 8px" }}>Python Ranking</td>
                        <td style={{ padding: "6px 8px" }}>Verify Python-only filtering + PyPI adjustments</td>
                        <td style={{ padding: "6px 8px" }}>53,885 repos, all Python, sorted, no duplicates, expected rank gaps</td>
                        <td style={{ padding: "6px 8px", color: "#6ee7b7" }}><strong>🟢 Passed</strong></td>
                    </tr>
                    <tr>
                        <td style={{ padding: "6px 8px" }}>Repo Metrics Consistency</td>
                        <td style={{ padding: "6px 8px" }}>created_at vs pushed_at, non-negative metrics</td>
                        <td style={{ padding: "6px 8px" }}>0.65% timestamp anomalies (non-critical), open_issues valid</td>
                        <td style={{ padding: "6px 8px", color: "#fcd34d" }}><strong>🟡 Minor warnings</strong></td>
                    </tr>
                    <tr>
                        <td style={{ padding: "6px 8px" }}>Metric Quality</td>
                        <td style={{ padding: "6px 8px" }}>Check missing/invalid values, distribution</td>
                        <td style={{ padding: "6px 8px" }}>No missing or negative fields, distributions reasonable</td>
                        <td style={{ padding: "6px 8px", color: "#6ee7b7" }}><strong>🟢 Clean</strong></td>
                    </tr>
                    </tbody>
                </table>
            </div>

            <h3 style={{ color: "#bae6fd", marginTop: "22px" }}>Final Validation Conclusion</h3>
            <p>All datasets are:</p>
            <ul style={{ marginLeft: "20px" }}>
                <li><strong>Correctly ordered</strong></li>
                <li><strong>Free of duplicates</strong></li>
                <li><strong>Structurally sound</strong></li>
                <li>Backed by <strong>high-integrity data</strong></li>
                <li><strong>Ready for frontend and analysis</strong></li>
            </ul>
            <p style={{ marginTop: "10px" }}>
                Full validation summary: <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>Seattle-Source-Ranker — Validation Summa.md</code>
            </p>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h2 style={{ color: "#7dd3fc" }}>Key Scripts</h2>
            <div style={{ overflowX: "auto", marginTop: "10px" }}>
                <table
                    style={{
                        width: "100%",
                        borderCollapse: "collapse",
                        fontSize: "0.9rem",
                    }}
                >
                    <thead>
                    <tr>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>File</th>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>Description</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td style={{ padding: "6px 8px" }}><code>json_to_csv.py</code></td>
                        <td style={{ padding: "6px 8px" }}>Utility converter</td>
                    </tr>
                    <tr>
                        <td style={{ padding: "6px 8px" }}><code>validate_repo_metrics.py</code></td>
                        <td style={{ padding: "6px 8px" }}>Checks raw metadata consistency and quality</td>
                    </tr>
                    <tr>
                        <td style={{ padding: "6px 8px" }}><code>validate_rankings.py</code></td>
                        <td style={{ padding: "6px 8px" }}>Validates ranking order, schema consistency, duplicates</td>
                    </tr>
                    </tbody>
                </table>
            </div>

            <h3 style={{ color: "#bae6fd", marginTop: "22px" }}>How to Run Validation</h3>
            <p>From project root:</p>
            <p style={{ marginTop: "10px" }}><strong>Validate repo metrics consistency & Quality:</strong></p>
            <pre
                style={{
                    background: "rgba(0,0,0,0.3)",
                    padding: "15px",
                    borderRadius: "10px",
                    marginTop: "5px",
                    color: "#9ecbff",
                    fontSize: "0.9rem",
                }}
            >
{`python json_to_csv.py
python validate_repo_metrics.py`}
            </pre>
            <p style={{ marginTop: "10px" }}><strong>Validate Overall Ranking & Python Ranking:</strong></p>
            <pre
                style={{
                    background: "rgba(0,0,0,0.3)",
                    padding: "15px",
                    borderRadius: "10px",
                    marginTop: "5px",
                    color: "#9ecbff",
                    fontSize: "0.9rem",
                }}
            >
{`python validate_rankings.py`}
            </pre>
            <p style={{ marginTop: "10px" }}>
                Outputs are directed to: <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>validation/validation_outputs/</code>
            </p>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h2 style={{ color: "#7dd3fc" }}>Project Structure</h2>
            <p>The core validation files are located under the following structure:</p>

            <pre
                style={{
                    background: "rgba(0,0,0,0.3)",
                    padding: "15px",
                    borderRadius: "10px",
                    marginTop: "15px",
                    overflowX: "auto",
                    color: "#9ecbff",
                    fontSize: "0.9rem",
                    lineHeight: "1.2",
                }}
            >
{`Seattle-Source-Ranker/
│
├── ……
├── validation/
│   ├── json_to_csv.py
│   ├── validate_repo_metrics.py
│   ├── validate_rankings.py
│   ├── if_seattle_Random_manual_sampling.xlsx
│   ├── README.md
│   └── validation_outputs/
│       ├── overall_ranking_validation.txt
│       ├── python_ranking_validation.txt
│       ├── repo_metrics_consistency.txt
│       ├── repo_metrics_quality.txt
│       ├── repo_metric_outliers.csv
│       └── Seattle-Source-Ranker — Validation Summa.md 
└── data/`}
            </pre>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h2 style={{ color: "#7dd3fc" }}>Manual Random Sampling Validation (Human-Audited Location Check)</h2>
            <p>
                To evaluate the real-world reliability of GitHub location metadata, we manually audited <strong>50 randomly sampled GitHub users</strong> and compared:
            </p>
            <ul style={{ marginLeft: "20px" }}>
                <li>GitHub profile location</li>
                <li>External profiles (LinkedIn, personal websites, company pages)</li>
                <li>Public employment / bio / project metadata</li>
            </ul>
            <p style={{ marginTop: "10px" }}>
                This cross-verification helps confirm whether GitHub location data is a <strong>valid proxy for real user location</strong> — an essential assumption for this project.
            </p>

            <h3 style={{ color: "#bae6fd", marginTop: "15px" }}>Sampling Results (50 Users)</h3>
            <div style={{ overflowX: "auto", marginTop: "10px" }}>
                <table
                    style={{
                        width: "100%",
                        borderCollapse: "collapse",
                        fontSize: "0.9rem",
                    }}
                >
                    <thead>
                    <tr>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>Category</th>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>Count</th>
                        <th style={{ borderBottom: "1px solid rgba(255,255,255,0.15)", textAlign: "left", padding: "6px 8px" }}>Percentage</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td style={{ padding: "6px 8px" }}>Matched (GitHub location = external profile)</td>
                        <td style={{ padding: "6px 8px" }}>44</td>
                        <td style={{ padding: "6px 8px" }}><strong>88%</strong></td>
                    </tr>
                    <tr>
                        <td style={{ padding: "6px 8px" }}>Mismatched (conflicts or unverifiable)</td>
                        <td style={{ padding: "6px 8px" }}>6</td>
                        <td style={{ padding: "6px 8px" }}><strong>12%</strong></td>
                    </tr>
                    </tbody>
                </table>
            </div>

            <h3 style={{ color: "#bae6fd", marginTop: "22px" }}>Visual Breakdown</h3>

            <pre
                style={{
                    background: "rgba(0,0,0,0.3)",
                    padding: "15px",
                    borderRadius: "10px",
                    marginTop: "15px",
                    overflowX: "auto",
                    color: "#9ecbff",
                    fontSize: "0.9rem",
                    lineHeight: "1.2",
                }}
            >
{`Matched      ████████████████████████████████████████  44 (88%)
Mismatched   ████                                      6 (12%)`}
            </pre>

            <h3 style={{ color: "#bae6fd", marginTop: "22px" }}>Interpretation of Mismatches (6 Users)</h3>
            <p>The 6 mismatches typically fell into the following categories:</p>
            <ul style={{ marginLeft: "20px" }}>
                <li><strong>1. Users who relocated but never updated GitHub</strong>
                    <ul style={{ listStyleType: 'circle', marginLeft: "20px", marginTop: "5px" }}>
                        <li>GitHub still shows “Seattle”</li>
                        <li>LinkedIn lists a new city (e.g., SF / NYC / remote)</li>
                    </ul>
                </li>
                <li><strong>2. Missing external references</strong>
                    <ul style={{ listStyleType: 'circle', marginLeft: "20px", marginTop: "5px" }}>
                        <li>No LinkedIn / personal website</li>
                        <li>No self-reported external location</li>
                        <li>Not strictly a mismatch, but unverifiable</li>
                    </ul>
                </li>
            </ul>

            <h3 style={{ color: "#bae6fd", marginTop: "22px" }}>Meaning for Our Project</h3>
            <p>An <strong>88% match rate</strong> demonstrates:</p>
            <ul style={{ marginLeft: "20px" }}>
                <li>GitHub user location is <strong>generally reliable</strong></li>
                <li>Filtering Seattle users based on GitHub metadata is <strong>statistically supported</strong></li>
                <li>The observed mismatch rate is <strong>reasonable</strong> in public datasets</li>
                <li>Manual sampling <strong>strengthens dataset credibility</strong></li>
            </ul>

            <h3 style={{ color: "#bae6fd", marginTop: "22px" }}>Sampling File</h3>
            <p>
                Details of the audit can be found in: <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>validation/if_seattle_Random_manual_sampling.xlsx</code>
            </p>
            <p>Contains fields such as:</p>
            <ul style={{ marginLeft: "20px" }}>
                <li>GitHub username</li>
                <li>GitHub location field</li>
                <li>External profile URL</li>
                <li>Match? (Yes / No)</li>
                <li>Notes on mismatch reasoning</li>
            </ul>

            <h3 style={{ color: "#bae6fd", marginTop: "22px" }}>Conclusion</h3>
            <p>
                This manual audit adds a <strong>human-verification layer</strong> on top of automated validation.
            </p>
            <p>
                Even with a 12% mismatch rate, our sampling <strong>strongly supports the use of GitHub location</strong> as a meaningful proxy for identifying Seattle-based developers.
            </p>
            <p>
                This provides <strong>additional real-world endorsement</strong> for the correctness and robustness of our dataset filtering logic.
            </p>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h2 style={{ color: "#7dd3fc" }}>Technologies</h2>
            <ul style={{ marginLeft: "20px" }}>
                <li>Python</li>
                <li>GitHub REST API</li>
                <li>Paginated JSON</li>
                <li>Validation pipelines</li>
            </ul>
        </>
    );

    // Helper component for the new (Results) content - UNCHANGED FROM PREVIOUS RESPONSE
    const ValidationResultsContent = () => (
        <>
            <h2 style={{ color: "#7dd3fc", marginBottom: "10px" }}>Validation Summary</h2>
            <p>
                This document summarizes all validation procedures performed on the project’s ranking data and raw GitHub metadata. It consolidates outputs from multiple validation scripts to provide a clear picture of <strong>dataset correctness</strong>, <strong>ordering consistency</strong>, and overall <strong>data quality</strong>.
            </p>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h3 style={{ color: "#bae6fd" }}>Overall Ranking Validation (Top 10,000 Repositories)</h3>
            <p>
                The overall ranking validation ensures that the top 10,000 GitHub repositories are correctly ordered and internally consistent.
            </p>
            <h4 style={{ color: "rgba(255,255,255,0.8)", marginTop: "10px" }}>Key Results:</h4>
            <ul style={{ marginLeft: "20px" }}>
                <li>Schema fully valid (<code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>schema_ok = True</code>)</li>
                <li>Successfully loaded all <strong>10,000</strong> ranked items</li>
                <li>No missing or <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>NaN</code> score values</li>
                <li>Score ordering strictly correct (<code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>is_sorted_desc = True</code>)</li>
                <li>No <strong>duplicate repositories</strong></li>
                <li><code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>global_rank</code> spans cleanly from 1 to 10,000</li>
                <li>No rank gaps or discontinuities</li>
                <li>Suitable for frontend consumption</li>
            </ul>
            <blockquote style={{ marginTop: "15px", opacity: 0.85 }}>
                <strong>Conclusion:</strong> The overall ranking dataset is <strong>perfectly valid</strong> and internally coherent. All entries follow expected ordering and uniqueness constraints.
            </blockquote>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h3 style={{ color: "#bae6fd" }}>Python + PyPI Ranking Validation</h3>
            <p>
                This ranking is a filtered subset of GitHub repositories that include Python projects, with optional PyPI-based score bonuses.
            </p>
            <h4 style={{ color: "rgba(255,255,255,0.8)", marginTop: "10px" }}>Key Results:</h4>
            <ul style={{ marginLeft: "20px" }}>
                <li><strong>53,885</strong> Python repositories included</li>
                <li>All entries have valid scores</li>
                <li>Score ordering correct across all entries</li>
                <li>No duplicate repositories</li>
                <li>All entries correctly identified as Python repositories</li>
                <li><code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>global_rank</code> is <strong>non-continuous</strong> (expected due to subset nature)</li>
                <li>Large <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>global_rank</code> gaps represent intervening non-Python repositories</li>
            </ul>
            <blockquote style={{ marginTop: "15px", opacity: 0.85 }}>
                <strong>Conclusion:</strong> The Python ranking is <strong>clean, consistent, and properly filtered</strong>. All entries adhere to ordering and type expectations. Non-continuous global ranks are valid because this ranking represents a subset of the overall dataset.
            </blockquote>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h3 style={{ color: "#bae6fd" }}>Repository Metrics Consistency Checks</h3>
            <p>Two structural checks were performed on raw GitHub metadata:</p>

            <h4 style={{ color: "rgba(255,255,255,0.8)", marginTop: "10px" }}>(<code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>created_at</code> vs <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>pushed_at</code>)</h4>
            <ul style={{ marginLeft: "20px" }}>
                <li><strong>432,421</strong> valid repositories</li>
                <li><strong>2,806</strong> invalid entries (~0.65%), handled as low-severity warnings</li>
                <li>Likely caused by upstream metadata inconsistencies or unusual repo history</li>
            </ul>

            <h4 style={{ color: "rgba(255,255,255,0.8)", marginTop: "10px" }}>(<code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>open_issues</code> non-negative)</h4>
            <ul style={{ marginLeft: "20px" }}>
                <li><strong>100% valid</strong></li>
                <li>No negative values found</li>
            </ul>

            <blockquote style={{ marginTop: "15px", opacity: 0.85 }}>
                <strong>Conclusion:</strong> Repository metadata is generally well-formed. Timestamp irregularities exist but are <strong>rare</strong> and not impactful to downstream ranking.
            </blockquote>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h3 style={{ color: "#bae6fd" }}>Repository Metrics Quality Summary</h3>
            <p>Quality statistics were generated for stars, forks, watchers, and open issues across <strong>432,421 repositories</strong>.</p>

            <h4 style={{ color: "rgba(255,255,255,0.8)", marginTop: "10px" }}>Key Results:</h4>
            <ul style={{ marginLeft: "20px" }}>
                <li>No <strong>missing values</strong> in any metrics</li>
                <li>No <strong>negative values</strong></li>
                <li>Metrics are statistically reasonable:
                    <ul style={{ listStyleType: 'circle', marginLeft: "20px", marginTop: "5px" }}>
                        <li>Stars: min=0, max=60761, mean=6.54, median=0</li>
                        <li>Forks: min=0, max=243374, mean=2.09, median=0</li>
                        <li>Watchers: min=0, max=1786, mean=1.29, median=1</li>
                        <li>Issues: min=0, max=1523, mean=0.99, median=0</li>
                    </ul>
                </li>
            </ul>
            <blockquote style={{ marginTop: "15px", opacity: 0.85 }}>
                <strong>Conclusion:</strong> All important repository metrics are <strong>structurally sound</strong> and free from errors. Data is suitable for use in the ranking algorithms without further cleaning.
            </blockquote>

            <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

            <h2 style={{ color: "#7dd3fc" }}>Final Conclusion</h2>

            <p>
                Across all validation components—ranking integrity, duplicate detection, sorting correctness, and raw metric health—the Seattle-Source-Ranker dataset is <strong>clean, reliable, and production-ready</strong>.
            </p>
            <p>
                The computed overall and Python rankings show correct ordering, no duplication, and robust schema consistency. All supporting metadata is sufficiently clean for use in scoring and frontend display.
            </p>
            <p>
                This validation confirms that the dataset can be <strong>safely used</strong> for further analysis and presentation.
            </p>
        </>
    );


    return (
        <div className="container">
            <Link to="/" className="back-btn">
                ← Back
            </Link>

            <header>
                <h1>Data Validation &amp; Reliability</h1>
                <p className="subtitle">
                    Ensuring accuracy, coverage, and trustworthiness of Seattle&apos;s open-source project ranking
                </p>
            </header>

            {/* BUTTON CONTAINER / TAB NAVIGATION */}
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '15px' }}>
                <button
                    style={getButtonStyle('method')}
                    onClick={() => setActiveSection('method')}
                >
                    Validation Methods
                </button>
                <button
                    style={getButtonStyle('results')}
                    onClick={() => setActiveSection('results')}
                >
                    Validation Results
                </button>
            </div>

            {/* CONTENT DISPLAY */}
            <div style={contentContainerStyle}>
                {activeSection === 'method' && <ValidationMethodsContent />}
                {activeSection === 'results' && <ValidationResultsContent />}
            </div>
        </div>
    );
}