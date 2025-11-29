// src/HomePage.js
import React from "react";
import { Link } from "react-router-dom";
import "./App.css";

export default function HomePage() {
    return (
        <div className="container home-container">

            <header
                className="home-header"
                style={{
                    justifyContent: "center",
                    background: "transparent",
                    boxShadow: "none"
                }}
            >
                <h1 className="home-title" style={{ color: "white" }}>
                    Seattle Source Ranker
                </h1>
            </header>

            {/* 卡片 1：總排行榜 */}
            <section className="home-card glass-card">
                <div className="home-card-text">
                    <h2 className="home-card-title" style={{color: "white"}}>
                        Overall Rankings
                    </h2>

                    <p className="home-card-subtitle" style={{color: "white"}}>
                        Top 10,000 open source projects from Seattle developers across all programming 
                        languages. View the elite leaderboard ranked by our multi-factor SSR scoring 
                        algorithm, with full search access to 400K+ repositories.
                    </p>

                    <p className="home-card-body" style={{color: "white"}}>
                        Rankings display the top 10,000 projects spanning JavaScript, Python, Java, Go, 
                        C++, and more. Use the search function to discover any project from our complete 
                        400K+ repository database. Our SSR algorithm combines GitHub stars, forks, 
                        recency, and project health metrics.
                    </p>

                    <div className="home-card-actions">
                        <Link to="/rankings" className="primary-btn glass-btn">
                            View Overall Rankings
                        </Link>
                    </div>
                </div>

                <div className="home-card-image">
                    <img src={`${process.env.PUBLIC_URL}/images/ssr.png`} alt="Seattle OSS Landscape"/>
                </div>
            </section>

            {/* 卡片 2：Python 專屬排行榜 */}
            <section className="home-card glass-card">
                <div className="home-card-text">
                    <h2 className="home-card-title" style={{color: "white"}}>
                        Python Rankings
                    </h2>

                <p className="home-card-subtitle" style={{color: "white"}}>
                    Dedicated rankings for Seattle&apos;s Python ecosystem with PyPI integration.
                    Projects published on PyPI receive a 10% score multiplier, rewarding packages
                    that contribute to Python&apos;s distribution ecosystem.
                </p>

                <p className="home-card-body" style={{color: "white"}}>
                    The 1.1× multiplier recognizes the effort required to package and publish
                    projects on PyPI, highlighting real-world packages available via pip install.
                </p>                    <div className="home-card-actions">
                        <Link to="/python-projects" className="primary-btn secondary glass-btn">
                            View Python Projects
                        </Link>
                    </div>
                </div>

                <div className="home-card-image">
                    <img src={`${process.env.PUBLIC_URL}/images/python.png`} alt="Python Logo"/>
                </div>
            </section>

            {/* Bottom Info Links */}
            <section className="home-info-links">
                <Link to="/scoring" className="info-link">
                    <div className="info-link-content">
                        <h3 className="info-link-title">SSR Scoring Methodology</h3>
                        <p className="info-link-desc">Learn how we combine popularity, quality, and activity metrics</p>
                    </div>
                    <span className="info-link-arrow">Learn More →</span>
                </Link>

                <Link to="/validation" className="info-link">
                    <div className="info-link-content">
                        <h3 className="info-link-title">Data Validation & Reliability</h3>
                        <p className="info-link-desc">Discover our multi-stage validation process ensuring accuracy</p>
                    </div>
                    <span className="info-link-arrow">Learn More →</span>
                </Link>
            </section>
        </div>
    );
}
