// src/ScoringPage.js
import React from "react";
import "./App.css";

export default function ScoringPage() {
    return (
        <div className="container">
            <header>
                <h1>SSR Scoring Methodology</h1>
                <p className="subtitle">
                    How Seattle Source Ranker combines popularity and quality into a single score
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
                    marginBottom: "40px"
                }}
            >
                {/* 1. Why a scoring system */}
                <h2 style={{ color: "#c5d1e0", marginBottom: "10px" }}>
                    1. Why a Scoring System?
                </h2>
                <p>
                    Seattle&#39;s open-source ecosystem is long-tailed: a few projects have tens of
                    thousands of stars, while many high-quality projects are smaller but actively
                    maintained. Simply sorting by GitHub stars would over-reward &quot;famous&quot;
                    projects and hide newer or niche but healthy ones.
                </p>
                <p style={{ marginTop: "8px" }}>
                    Seattle Source Ranker (SSR) uses a multi-factor score that combines{" "}
                    <strong>popularity</strong> (stars / forks / watchers) with{" "}
                    <strong>quality and maintenance signals</strong> (age, activity, health).
                    The goal is to answer:
                </p>
                <ul style={{ marginTop: "8px", marginLeft: "20px" }}>
                    <li>Which projects are widely used and recognized?</li>
                    <li>Which projects are actively maintained and healthy?</li>
                    <li>Which projects are influential within their language ecosystem?</li>
                </ul>

                {/* 2. Overview of factors */}
                <h2 style={{ color: "#c5d1e0", marginTop: "30px" }}>
                    2. Overview of Score Factors
                </h2>
                <p>
                    Each project receives an SSR score between roughly <strong>0–10,000</strong>,
                    built from six components:
                </p>

                <ul style={{ marginLeft: "20px" }}>
                    <li>
                        <strong>Stars (40%)</strong> – primary popularity / community recognition
                    </li>
                    <li>
                        <strong>Forks (20%)</strong> – depth of engagement and derivative work
                    </li>
                    <li>
                        <strong>Watchers (10%)</strong> – ongoing interest and monitoring
                    </li>
                    <li>
                        <strong>Age (10%)</strong> – project maturity (sweet spot around 3–5 years)
                    </li>
                    <li>
                        <strong>Activity (10%)</strong> – recency of updates (last push time)
                    </li>
                    <li>
                        <strong>Health (10%)</strong> – issue management relative to popularity
                    </li>
                </ul>

                <p style={{ marginTop: "10px" }}>
                    The first three are <strong>base popularity metrics</strong> (70% total).
                    The last three are <strong>quality factors</strong> (30% total) that prevent
                    abandoned but famous projects from dominating the rankings.
                </p>

                {/* 3. Log scaling */}
                <h2 style={{ color: "#c5d1e0", marginTop: "30px" }}>
                    3. Logarithmic Scaling of GitHub Metrics
                </h2>
                <p>
                    GitHub metrics are extremely skewed: going from 10 → 100 stars is much harder
                    than 1000 → 1100. To avoid a few huge projects overwhelming the whole list,
                    SSR applies base-10 logarithmic scaling and normalization for stars, forks,
                    and watchers:
                </p>

                <pre
                    style={{
                        background: "rgba(0,0,0,0.3)",
                        padding: "15px",
                        borderRadius: "10px",
                        marginTop: "15px",
                        color: "#9ecbff",
                        overflowX: "auto"
                    }}
                >{`normalized_metric = log10(raw_value + 1) / log10(max_value)`}</pre>

                <p style={{ marginTop: "10px" }}>
                    Here <code>max_value</code> is a fixed upper bound (for example, 100,000 stars
                    or 10,000 forks) chosen from observed Seattle projects and global GitHub
                    distributions. This keeps scores numerically stable and comparable over time.
                </p>

                {/* 4. Final score formula */}
                <h2 style={{ color: "#c5d1e0", marginTop: "30px" }}>
                    4. Final Score Formula
                </h2>
                <p>The SSR score combines the six factors into a single number:</p>

                <pre
                    style={{
                        background: "rgba(0,0,0,0.3)",
                        padding: "15px",
                        borderRadius: "10px",
                        marginTop: "15px",
                        color: "#9ecbff",
                        overflowX: "auto"
                    }}
                >{`Score = (
    log10(stars    + 1) / log10(100000) * 0.40 +
    log10(forks    + 1) / log10(10000)  * 0.20 +
    log10(watchers + 1) / log10(10000)  * 0.10 +
    age_factor()      * 0.10 +
    activity_factor() * 0.10 +
    health_factor()   * 0.10
) * 10000`}</pre>

                <p style={{ marginTop: "10px" }}>
                    The final multiplication by <code>10000</code> is purely for readability, so
                    typical projects land in the range <strong>hundreds to several thousands</strong>.
                </p>

                {/* 5. Factor definitions */}
                <h2 style={{ color: "#c5d1e0", marginTop: "30px" }}>
                    5. How Each Factor is Interpreted
                </h2>

                <h3 style={{ color: "#d4def2", marginTop: "10px" }}>5.1 Base Popularity (70%)</h3>
                <ul style={{ marginLeft: "20px" }}>
                    <li>
                        <strong>Stars (40%)</strong> – main signal for community adoption.
                        After log scaling, going from 10 → 100 stars still matters, but
                        10,000 → 11,000 stars has a smaller relative impact.
                    </li>
                    <li>
                        <strong>Forks (20%)</strong> – projects that are used as a base for other
                        work. High-fork projects are often libraries, frameworks, or templates that
                        influence many downstream repos.
                    </li>
                    <li>
                        <strong>Watchers (10%)</strong> – long-term interest from contributors or
                        users who follow the project over time.
                    </li>
                </ul>

                <h3 style={{ color: "#d4def2", marginTop: "18px" }}>5.2 Quality & Maintenance (30%)</h3>
                <ul style={{ marginLeft: "20px" }}>
                    <li>
                        <strong>age_factor()</strong> – projects between ~3–5 years old receive the
                        highest score; extremely new projects (a few weeks) and very old but inactive
                        projects are slightly penalized.
                    </li>
                    <li>
                        <strong>activity_factor()</strong> – based on how recently{" "}
                        <code>pushed_at</code> was updated. Projects with commits in the last
                        3–6 months receive the strongest bonus, while multi-year inactivity reduces
                        this component.
                    </li>
                    <li>
                        <strong>health_factor()</strong> – looks at open issues relative to popularity
                        (for example, issues per 1000 stars) and whether the project appears
                        abandoned or overloaded with unresolved problems.
                    </li>
                </ul>

                {/* 6. Overall vs language-specific */}
                <h2 style={{ color: "#c5d1e0", marginTop: "30px" }}>
                    6. Overall vs Language-Specific Rankings
                </h2>
                <p>
                    Once SSR scores are computed, projects are ranked in two main ways:
                </p>
                <ul style={{ marginLeft: "20px" }}>
                    <li>
                        <strong>Overall ranking</strong> – all languages combined, answering:
                        &quot;What are the most influential projects across Seattle?&quot;
                    </li>
                    <li>
                        <strong>Language-specific rankings</strong> – separate leaderboards for the
                        11 major languages detected by the pipeline.
                    </li>
                </ul>
                <p style={{ marginTop: "8px" }}>
                    This allows you to compare a small but high-quality Python library with other
                    Python projects, instead of competing directly against huge JavaScript or Go
                    repositories.
                </p>

                {/* 7. Why this is fairer than raw stars */}
                <h2 style={{ color: "#c5d1e0", marginTop: "30px" }}>
                    7. Why This Approach is Fairer than Raw Stars
                </h2>
                <p>
                    Compared to naive &quot;sort by stars&quot;, the SSR methodology:
                </p>
                <ul style={{ marginLeft: "20px" }}>
                    <li>
                        <strong>Reduces domination</strong> by very old, very large projects through
                        log scaling and age / activity factors.
                    </li>
                    <li>
                        <strong>Highlights actively maintained work</strong> by rewarding recent
                        pushes and healthy issue management.
                    </li>
                    <li>
                        <strong>Balances big and small projects</strong> so that a well-maintained
                        2k-star library can rank near a 10k-star but semi-abandoned project.
                    </li>
                    <li>
                        <strong>Remains transparent</strong> – every factor and weight is explicitly
                        documented and can be recomputed from raw GitHub data.
                    </li>
                </ul>

                {/* 8. Reproducibility note */}
                <h2 style={{ color: "#c5d1e0", marginTop: "30px" }}>
                    8. Reproducibility & Future Extensions
                </h2>
                <p>
                    All factors used in the SSR score come directly from the collected GitHub data
                    (stars, forks, watchers, timestamps, issue counts) and can be recomputed
                    offline from the exported JSON files under <code>data/</code>. The scoring
                    function is intentionally simple enough to be:
                </p>
                <ul style={{ marginLeft: "20px" }}>
                    <li>Reimplemented in Python, R, or SQL for independent verification</li>
                    <li>Adjusted with different weights for custom experiments</li>
                    <li>Extended with new factors such as contributor diversity or test coverage</li>
                </ul>

                <p style={{ marginTop: "10px" }}>
                    Future versions of Seattle Source Ranker may experiment with{" "}
                    <strong>time-decayed stars</strong>, <strong>contributor activity</strong>,
                    or <strong>ecosystem impact</strong> while keeping the core principles of
                    transparency, fairness, and reproducibility.
                </p>

                {/* SECTION 7 — Example */}
                <h2 style={{ color: "#c5d1e0", marginTop: "30px" }}>
                    9. Example: Scoring a Sample Project
                </h2>

                <pre
                    style={{
                        background: "rgba(0,0,0,0.3)",
                        padding: "15px",
                        borderRadius: "10px",
                        color: "#9ecbff"
                    }}
                >
{`Example Project:
stars = 4200
forks = 330
watchers = 210
age_factor = 0.82
activity_factor = 0.91
health_factor = 0.77

Final Score ≈ 8432`}
                </pre>

                <p>
                    Small projects with strong maintenance activity often rank higher than older,
                    abandoned projects with more stars.
                </p>

            </div>
        </div>
    );
}