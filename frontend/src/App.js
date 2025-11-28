// src/App.js
import React from "react";
import {
    BrowserRouter as Router,
    Routes,
    Route
} from "react-router-dom";
import "./App.css";

import HomePage from "./HomePage";
import RankingsPage from "./RankingsPage";
import ScoringPage from "./ScoringPage";
import ValidationPage from "./ValidationPage";
import PythonProjectsPage from "./PythonProjectsPage";

export default function App() {
    return (
        <Router>
            <div className="app-root">
                <Routes>
                    <Route path="/" element={<HomePage />} />

                    <Route path="/rankings" element={<RankingsPage />} />

                    <Route path="/python-projects" element={<PythonProjectsPage />} />

                    <Route path="/scoring" element={<ScoringPage />} />
                    <Route path="/validation" element={<ValidationPage />} />
                </Routes>
            </div>
        </Router>
    );
}
