// src/App.js
import React, { useEffect } from "react";
import {
    BrowserRouter as Router,
    Routes,
    Route,
    useLocation
} from "react-router-dom";
import "./App.css";

import HomePage from "./HomePage";
import OverallRankingsPage from "./OverallRankingsPage";
import ScoringPage from "./ScoringPage";
import ValidationPage from "./ValidationPage";
import PythonRankingsPage from "./PythonRankingsPage";

function ScrollToTop() {
    const { pathname } = useLocation();

    useEffect(() => {
        // Only scroll to top when navigating to home page
        if (pathname === '/') {
            window.scrollTo({
                top: 0,
                left: 0,
                behavior: 'smooth'
            });
        }
    }, [pathname]);

    return null;
}

export default function App() {
    return (
        <Router basename="/Seattle-Source-Ranker">
            <div className="app-root">
                <ScrollToTop />
                <Routes>
                    <Route path="/" element={<HomePage />} />

                    <Route path="/rankings" element={<OverallRankingsPage />} />

                    <Route path="/python-projects" element={<PythonRankingsPage />} />

                    <Route path="/scoring" element={<ScoringPage />} />
                    <Route path="/validation" element={<ValidationPage />} />
                </Routes>
            </div>
        </Router>
    );
}
