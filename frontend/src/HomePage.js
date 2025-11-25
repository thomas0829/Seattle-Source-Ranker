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
                    Rankings
                </h1>
            </header>

            {/* 卡片 1：Seattle Source Ranker */}
            <section className="home-card glass-card">
                <div className="home-card-text">
                    <h2 className="home-card-title" style={{color: "white"}}>
                        Seattle Source Ranker
                    </h2>

                    <p className="home-card-subtitle" style={{color: "white"}}>
                        A data-driven ranking of open source projects created by developers
                        in the Seattle area. Discover influential repositories, explore
                        tech stacks, and understand our multi-factor SSR scoring model.
                    </p>

                    <p className="home-card-body" style={{color: "white"}}>
                        Seattle Source Ranker aggregates 400K+ repositories and 20K+ users
                        using a distributed Celery + Redis pipeline, GitHub GraphQL/REST
                        APIs, and a transparent scoring algorithm that blends popularity,
                        recency and project health.
                    </p>

                    <div className="home-card-actions">
                        <Link to="/rankings" className="primary-btn glass-btn">
                            Explore Rankings
                        </Link>
                    </div>
                </div>

                <div className="home-card-image">
                    <img src="/images/ssr.png" alt="Seattle OSS Landscape"/>
                </div>
            </section>

            {/* 卡片 2：Python Projects */}
            <section className="home-card glass-card">
                <div className="home-card-text">
                    <h2 className="home-card-title" style={{color: "white"}}>
                        Python Projects
                    </h2>

                    <p className="home-card-subtitle" style={{color: "white"}}>
                        A curated view of Python-heavy repositories in Seattle&apos;s
                        developer community, focusing on data, ML, backend services, and
                        developer tooling.
                    </p>

                    <p className="home-card-body" style={{color: "white"}}>
                        This section will highlight Python ecosystems across FastAPI,
                        Django, data pipelines, ML experimentation, and infra tooling.
                        You&apos;ll be able to filter by domain and quickly see which
                        projects are the most active and impactful.
                    </p>

                    <div className="home-card-actions">
                        <Link to="/python-projects" className="primary-btn secondary glass-btn">
                            View Python Projects
                        </Link>
                    </div>
                </div>

                <div className="home-card-image">
                    <img src="/images/python.png" alt="Python Logo"/>
                </div>
            </section>

            {/* 底部按钮 */}
            <section className="home-bottom-links glass-soft">
            <h3 className="home-bottom-title" style={{color: "white" }}>
                    Learn more about SSR
                </h3>
                <div className="home-bottom-buttons">
                    <Link to="/scoring" className="language-tab home-nav-tab glass-btn-mini">
                        SSR Scoring Methodology
                    </Link>
                    <Link to="/validation" className="language-tab home-nav-tab glass-btn-mini">
                        Data Validation & Reliability
                    </Link>
                </div>
            </section>
        </div>
    );
}
