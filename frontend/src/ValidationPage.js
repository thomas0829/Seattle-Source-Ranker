import React, { useEffect } from "react";
import "./App.css";
import { Link } from "react-router-dom";

export default function ValidationPage() {
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);
    
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

            <div
                style={{
                    background: "rgba(255,255,255,0.05)",
                    padding: "25px 30px",
                    borderRadius: "15px",
                    backdropFilter: "blur(15px)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: "rgba(255,255,255,0.85)",
                    lineHeight: "1.7",
                    marginTop: "10px",
                }}
            >
                {/* Intro */}
                <p>
                    Seattle Source Ranker uses a multi-stage validation process to guarantee that our dataset accurately
                    represents Seattle&apos;s active GitHub developer community. This page explains{" "}
                    <strong>what we collect</strong>, <strong>how we verify it</strong>, and{" "}
                    <strong>why the methodology produces reliable results</strong>.
                </p>

                <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

                {/* 1. Baseline User File */}
                <h2 style={{ color: "#7dd3fc", marginBottom: "10px" }}>1. Baseline User File</h2>
                <p>
                    Each automated run produces a <strong>baseline file</strong> that contains all discovered Seattle GitHub
                    users.
                </p>
                <p>
                    Latest example:{" "}
                    <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>
                        seattle_users_20251120_005135.json
                    </code>
                </p>

                <pre
                    style={{
                        background: "rgba(0,0,0,0.3)",
                        padding: "15px",
                        borderRadius: "10px",
                        marginTop: "15px",
                        overflowX: "auto",
                        color: "#9ecbff",
                        fontSize: "0.9rem",
                    }}
                >
{`{
  "total_users": 28203,
  "collected_at": "2025-11-20T00:51:35-08:00",
  "query_strategy": "graphql multi-filter",
  "filters_used": 76,
  "usernames": [
    "jmonty42",
    "pvomelveny",
    "Dhani109",
    "pheId",
    "lucaswin-amzn",
    ...
  ]
}`}
        </pre>

                <h3 style={{ color: "#bae6fd", marginTop: "22px" }}>Fields</h3>
                <div style={{ overflowX: "auto" }}>
                    <table
                        style={{
                            width: "100%",
                            borderCollapse: "collapse",
                            marginTop: "10px",
                            fontSize: "0.9rem",
                        }}
                    >
                        <thead>
                        <tr>
                            <th
                                style={{
                                    borderBottom: "1px solid rgba(255,255,255,0.15)",
                                    textAlign: "left",
                                    padding: "6px 8px",
                                }}
                            >
                                Field
                            </th>
                            <th
                                style={{
                                    borderBottom: "1px solid rgba(255,255,255,0.15)",
                                    textAlign: "left",
                                    padding: "6px 8px",
                                }}
                            >
                                Meaning
                            </th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                            <td style={{ padding: "6px 8px" }}><code>total_users</code></td>
                            <td style={{ padding: "6px 8px" }}>Total Seattle users detected in this run (28,203)</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}><code>collected_at</code></td>
                            <td style={{ padding: "6px 8px" }}>Timestamp of the collection (PST)</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}><code>query_strategy</code></td>
                            <td style={{ padding: "6px 8px" }}>Discovery method (GraphQL multi-filter)</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}><code>filters_used</code></td>
                            <td style={{ padding: "6px 8px" }}>Number of location filters used (76)</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}><code>usernames</code></td>
                            <td style={{ padding: "6px 8px" }}>
                                Username list of all discovered Seattle developers
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>

                <p style={{ marginTop: "14px" }}>
                    This baseline enables <strong>coverage validation</strong>, <strong>reproducibility</strong>, and{" "}
                    <strong>cross-checking</strong> against external data sources.
                </p>

                <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

                {/* 2. Coverage Validation */}
                <h2 style={{ color: "#7dd3fc" }}>2. Coverage Validation</h2>
                <p>
                    We verify that the system captures <strong>nearly all meaningful Seattle developers</strong>, rather than
                    every single account (including empty or dormant ones).
                </p>

                <h3 style={{ color: "#bae6fd", marginTop: "14px" }}>User Inclusion Logic</h3>
                <p>A user is included if:</p>
                <ul style={{ marginLeft: "20px" }}>
                    <li>They have <strong>≥ 10 public repositories</strong>, or</li>
                    <li>They have <strong>1–9 repositories</strong> and <strong>&gt; 10 followers</strong></li>
                </ul>

                <p style={{ marginTop: "10px" }}>
                    This ensures the dataset focuses on <strong>active or influential contributors</strong> while excluding empty,
                    spam, or abandoned accounts.
                </p>

                <h3 style={{ color: "#bae6fd", marginTop: "16px" }}>Coverage Check Steps</h3>
                <ol style={{ marginLeft: "20px" }}>
                    <li>Compare the baseline file (28,203 users) with a separate validation username list</li>
                    <li>Identify missing or mismatched usernames</li>
                    <li>Inspect GitHub API logs for failures and rate-limit errors</li>
                    <li>Re-fetch missing accounts to confirm if they are valid, renamed, or temporarily inaccessible</li>
                </ol>

                <blockquote style={{ marginTop: "15px", opacity: 0.85 }}>
                    <strong>Result (v3.1):</strong>{" "}
                    <span style={{ fontWeight: 600 }}>Estimated meaningful coverage: 97%+</span>.
                    The dataset reliably mirrors the active GitHub community in Seattle.
                </blockquote>

                <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

                {/* 3. Repository-Level Validation */}
                <h2 style={{ color: "#7dd3fc" }}>3. Repository-Level Validation</h2>
                <p>
                    For each included user, we validate their repositories to ensure metadata accuracy and language
                    classification quality.
                </p>

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
                            <th
                                style={{
                                    borderBottom: "1px solid rgba(255,255,255,0.15)",
                                    textAlign: "left",
                                    padding: "6px 8px",
                                }}
                            >
                                Validation Item
                            </th>
                            <th
                                style={{
                                    borderBottom: "1px solid rgba(255,255,255,0.15)",
                                    textAlign: "left",
                                    padding: "6px 8px",
                                }}
                            >
                                Description
                            </th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Repo count match</td>
                            <td style={{ padding: "6px 8px" }}>
                                Compare GitHub live repository count vs. collected count
                            </td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Metadata correctness</td>
                            <td style={{ padding: "6px 8px" }}>
                                Verify stars / forks / watchers match GitHub API responses
                            </td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Timestamps</td>
                            <td style={{ padding: "6px 8px" }}>
                                Ensure <code>created_at</code> and <code>pushed_at</code> are valid and consistent
                            </td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Language classification</td>
                            <td style={{ padding: "6px 8px" }}>
                                Confirm the primary language aligns with GitHub&apos;s metadata and classification rules
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>

                <p style={{ marginTop: "10px" }}>
                    For each run, <strong>100–200 repositories</strong> are randomly sampled and revalidated directly against the
                    GitHub API to spot any drift or inconsistencies.
                </p>

                <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

                {/* 4. Scoring Validation */}
                <h2 style={{ color: "#7dd3fc" }}>4. Scoring Validation</h2>
                <p>
                    To ensure <strong>transparency</strong> and <strong>fair rankings</strong>, we verify the entire scoring
                    pipeline, not just the final numbers.
                </p>

                <h3 style={{ color: "#bae6fd", marginTop: "14px" }}>What we validate</h3>
                <ul style={{ marginLeft: "20px" }}>
                    <li>Logarithmic scaling is applied correctly to stars, forks, and watchers</li>
                    <li>All six factors (stars, forks, watchers, age, activity, health) are computed correctly</li>
                    <li>Weights sum to exactly <code>1.0</code></li>
                    <li>Score distribution is stable and predictable across runs</li>
                    <li>Very large and very small projects behave reasonably under the scoring model</li>
                </ul>

                <h3 style={{ color: "#bae6fd", marginTop: "14px" }}>Cross-check</h3>
                <p>
                    We manually recompute scores for <strong>50 randomly selected projects</strong> and compare them with the
                    system output.
                </p>

                <blockquote style={{ marginTop: "15px", opacity: 0.85 }}>
                    <strong>Result:</strong> <span style={{ fontWeight: 600 }}>100% match</span> between manual and automated
                    calculations.
                </blockquote>

                <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

                {/* 5. Reliability & Error Recovery */}
                <h2 style={{ color: "#7dd3fc" }}>5. Reliability &amp; Error Recovery</h2>
                <p>
                    The distributed collector (8 Celery workers, 16 parallel tasks) is designed for{" "}
                    <strong>robustness under API limits</strong> and transient failures.
                </p>

                <ul style={{ marginLeft: "20px" }}>
                    <li>Automatic retry on GitHub API failures</li>
                    <li>Token rotation across 6 GitHub tokens</li>
                    <li>Logging of failed usernames and repository fetches</li>
                    <li>Ability to re-run failed tasks only</li>
                    <li>Daily automated full-collection at midnight Seattle time (PST)</li>
                </ul>

                <p style={{ marginTop: "10px" }}>We actively track the following reliability signals:</p>

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
                            <th
                                style={{
                                    borderBottom: "1px solid rgba(255,255,255,0.15)",
                                    textAlign: "left",
                                    padding: "6px 8px",
                                }}
                            >
                                Item
                            </th>
                            <th
                                style={{
                                    borderBottom: "1px solid rgba(255,255,255,0.15)",
                                    textAlign: "left",
                                    padding: "6px 8px",
                                }}
                            >
                                Purpose
                            </th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>User-level failures</td>
                            <td style={{ padding: "6px 8px" }}>Detect unreachable, renamed, or deleted accounts</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Repo-level failures</td>
                            <td style={{ padding: "6px 8px" }}>Identify GitHub API inconsistencies or transient errors</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Token health</td>
                            <td style={{ padding: "6px 8px" }}>Detect expired, throttled, or rate-limited tokens</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Network issues</td>
                            <td style={{ padding: "6px 8px" }}>Identify transient connectivity and timeout problems</td>
                        </tr>
                        </tbody>
                    </table>
                </div>

                <p style={{ marginTop: "10px" }}>
                    These systems keep the dataset <strong>stable</strong>, <strong>fresh</strong>, and{" "}
                    <strong>operationally reliable</strong> across daily runs.
                </p>

                <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

                {/* 6. Reproducibility */}
                <h2 style={{ color: "#7dd3fc" }}>6. Reproducibility</h2>
                <p>All validation steps can be reproduced locally using the same inputs and scripts:</p>

                <pre
                    style={{
                        background: "rgba(0,0,0,0.3)",
                        padding: "15px",
                        borderRadius: "10px",
                        marginTop: "15px",
                        color: "#9ecbff",
                        fontSize: "0.9rem",
                    }}
                >
{`python validate_users.py --baseline seattle_users_20251120_005135.json
python validate_repos.py --sample-size 200
python validate_scores.py --projects-sample 50`}
        </pre>

                <p style={{ marginTop: "10px" }}>
                    Validation scripts are organized under a dedicated{" "}
                    <code style={{ background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "4px" }}>/validation/</code>{" "}
                    directory so that other researchers and engineers can re-run the exact same checks.
                </p>

                <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "24px 0" }} />

                {/* Summary */}
                <h2 style={{ color: "#7dd3fc" }}>Validation Summary</h2>

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
                            <th
                                style={{
                                    borderBottom: "1px solid rgba(255,255,255,0.15)",
                                    textAlign: "left",
                                    padding: "6px 8px",
                                }}
                            >
                                Aspect
                            </th>
                            <th
                                style={{
                                    borderBottom: "1px solid rgba(255,255,255,0.15)",
                                    textAlign: "left",
                                    padding: "6px 8px",
                                }}
                            >
                                Status
                            </th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>User Coverage</td>
                            <td style={{ padding: "6px 8px" }}>
                                28,203 users · <strong>97%+ completeness</strong>
                            </td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Repo Coverage</td>
                            <td style={{ padding: "6px 8px" }}>98% metadata correctness (sampled)</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Scoring Accuracy</td>
                            <td style={{ padding: "6px 8px" }}>100% match in manual verification</td>
                        </tr>
                        <tr>
                            <td style={{ padding: "6px 8px" }}>Reliability</td>
                            <td style={{ padding: "6px 8px" }}>
                                Stable across distributed worker system with daily full re-runs
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>

                <p style={{ marginTop: "14px" }}>
                    Seattle Source Ranker is designed to be <strong>transparent</strong>, <strong>accountable</strong>, and{" "}
                    <strong>academically reliable</strong>, so that rankings can be trusted by students, recruiters, and
                    researchers alike.
                </p>
            </div>
        </div>
    );
}
