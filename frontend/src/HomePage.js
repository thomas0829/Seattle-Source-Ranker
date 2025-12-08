// src/HomePage.js
import React, { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import "./App.css";

export default function HomePage() {
    const hasRestoredRef = useRef(false);
    
    // Save scroll position before unload (for F5 refresh)
    useEffect(() => {
        const handleBeforeUnload = () => {
            sessionStorage.setItem('homeScrollPosition', window.pageYOffset.toString());
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, []);
    
    // Restore scroll position after mount (only if coming from F5 refresh)
    useEffect(() => {
        const savedScrollPosition = sessionStorage.getItem('homeScrollPosition');
        if (savedScrollPosition && !hasRestoredRef.current) {
            hasRestoredRef.current = true;
            setTimeout(() => {
                window.scrollTo({ top: parseInt(savedScrollPosition, 10), behavior: 'smooth' });
                sessionStorage.removeItem('homeScrollPosition');
            }, 100);
        } else if (!savedScrollPosition) {
            // First time entering page - scroll to top
            window.scrollTo(0, 0);
        }
    }, []);
    
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

            {/* Card 1: Overall Rankings */}
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
                        Rankings display the top 10,000 projects across 10 major languages: JavaScript, 
                        Python, HTML, Java, TypeScript, C#, Ruby, CSS, C++, and Jupyter Notebook. 
                        Use the search function to discover any project from our complete 400K+ repository 
                        database. Our SSR algorithm combines GitHub stars, forks, recency, and project 
                        health metrics.
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

            {/* Card 2: Python Rankings */}
            <section className="home-card glass-card">
                <div className="home-card-text">
                    <h2 className="home-card-title" style={{color: "white"}}>
                        Python Rankings
                    </h2>

                <p className="home-card-subtitle" style={{color: "white"}}>
                    Dedicated rankings for Seattle&apos;s Python ecosystem with tiered PyPI integration.
                    Projects published on PyPI receive a 5% bonus, with Top 15k globally-downloaded
                    packages earning an additional 10% bonus (15.5% total).
                </p>

                <p className="home-card-body" style={{color: "white"}}>
                    The tiered system recognizes both PyPI publication (×1.05 for ~1,071 packages) and
                    global impact (×1.10 additional for ~28 Top 15k packages). Look for rainbow PyPI
                    badges and luxury gold-purple Top 15k badges.
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
