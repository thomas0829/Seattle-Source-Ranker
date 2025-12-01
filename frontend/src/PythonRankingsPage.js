// src/PythonProjectsPage.js
import React, { useState, useEffect, useMemo, useRef } from "react";
import "./App.css";
import { Link } from "react-router-dom";

// Scoring configuration - Multiplicative bonus approach
const GITHUB_WEIGHT = 1.0;       // 100% of base score
const PYPI_BONUS = 0.1;          // +10% multiplier for PyPI projects

// Current formula: finalScore = baseScore * (1.0 + 0.1) = baseScore * 1.1
// Future: Can change to weighted average by using separate weights for GitHub/PyPI components

export default function PythonRankingsPage() {
    const [projects, setProjects] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [metadata, setMetadata] = useState(null);
    const [totalProjects, setTotalProjects] = useState(0);
    const [tooltipPosition, setTooltipPosition] = useState({});
    const [hoveredProject, setHoveredProject] = useState(null);
    const [searchSuggestions, setSearchSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
    const [pageInput, setPageInput] = useState(null);
    const [isScrolling, setIsScrolling] = useState(false);
    const timeoutRef = useRef(null);
    const searchTimeoutRef = useRef(null);
    const searchWrapperRef = useRef(null);
    const scrollTimeoutRef = useRef(null);
    const projectsPerPage = 50;

    // Detect scrolling to pause background loading
    useEffect(() => {
        const handleScroll = () => {
            setIsScrolling(true);
            if (scrollTimeoutRef.current) {
                clearTimeout(scrollTimeoutRef.current);
            }
            scrollTimeoutRef.current = setTimeout(() => {
                setIsScrolling(false);
            }, 150);
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => {
            window.removeEventListener('scroll', handleScroll);
            if (scrollTimeoutRef.current) {
                clearTimeout(scrollTimeoutRef.current);
            }
        };
    }, []);

    useEffect(() => {
        const loadData = async () => {
            try {
                // Load metadata
                const metadataRes = await fetch(`${process.env.PUBLIC_URL}/metadata.json`);
                const metadataData = await metadataRes.json();
                setMetadata(metadataData);
                
                // Set total projects count from metadata
                const pythonTotal = metadataData.languages.Python?.total || 0;
                setTotalProjects(pythonTotal);
                
                // Load PyPI data
                let pypiData = null;
                try {
                    const pypiRes = await fetch(`${process.env.PUBLIC_URL}/data/seattle_pypi_projects.json`);
                    pypiData = await pypiRes.json();
                } catch (error) {
                    console.warn("PyPI data not available:", error);
                    pypiData = { projects: [] };
                }
                
                // Build PyPI lookup map
                const pypiMap = new Map();
                pypiData.projects.forEach(p => {
                    const key = `${p.owner}/${p.name}`.toLowerCase();
                    pypiMap.set(key, p);
                });
                
                // Load first 10 pages for quick display
                const pythonPages = metadataData.languages.Python?.pages || 0;
                const initialPages = Math.min(10, pythonPages);
                const initialPromises = [];
                
                for (let i = 1; i <= initialPages; i++) {
                    initialPromises.push(
                        fetch(`${process.env.PUBLIC_URL}/pages/python/page_${i}.json`)
                            .then(res => res.json())
                            .catch(() => [])
                    );
                }
                
                const firstBatch = await Promise.all(initialPromises);
                const allProjects = [];
                firstBatch.forEach(pageData => {
                    allProjects.push(...pageData);
                });
                
                // Calculate initial scores and display first 10 pages
                let scoredProjects = allProjects.map(proj => {
                    const [owner, projectName] = proj.name.split('/');
                    const key = proj.name.toLowerCase();
                    const onPypi = pypiMap.has(key);
                    const baseScore = proj.score || 0;
                    // PyPI projects get 10% bonus (multiplicative)
                    const finalScore = baseScore * (GITHUB_WEIGHT + (onPypi ? PYPI_BONUS : 0));
                    
                    return {
                        ...proj,
                        owner: owner,
                        name: projectName,
                        full_name: proj.name,
                        url: proj.html_url,
                        original_score: baseScore,
                        final_score: Math.round(finalScore),
                        on_pypi: onPypi
                    };
                });
                
                scoredProjects.sort((a, b) => {
                    // Primary: sort by score (descending)
                    if (b.final_score !== a.final_score) {
                        return b.final_score - a.final_score;
                    }
                    // Secondary: PyPI projects rank higher when scores are equal
                    if (a.on_pypi !== b.on_pypi) {
                        return b.on_pypi ? 1 : -1;
                    }
                    // Tertiary: alphabetical by name
                    return a.full_name.localeCompare(b.full_name);
                });
                // Add global rank
                scoredProjects.forEach((proj, idx) => {
                    proj.global_rank = idx + 1;
                });
                setProjects(scoredProjects);
                setLoading(false);
                
                // Load remaining pages in background
                if (pythonPages > initialPages && !isScrolling) {
                    const batchSize = 50;
                    for (let batchStart = initialPages + 1; batchStart <= pythonPages; batchStart += batchSize) {
                        // Check if scrolling before each batch
                        if (isScrolling) {
                            console.log('⏸️ Pausing background loading due to scroll');
                            break;
                        }
                        
                        const batchEnd = Math.min(batchStart + batchSize - 1, pythonPages);
                        const batchPromises = [];
                        
                        for (let i = batchStart; i <= batchEnd; i++) {
                            batchPromises.push(
                                fetch(`${process.env.PUBLIC_URL}/pages/python/page_${i}.json`)
                                    .then(res => res.json())
                                    .catch(() => [])
                            );
                        }
                        
                        const batchPages = await Promise.all(batchPromises);
                        batchPages.forEach(pageData => {
                            allProjects.push(...pageData);
                        });
                        
                        // Recalculate and update all projects
                        scoredProjects = allProjects.map(proj => {
                            const [owner, projectName] = proj.name.split('/');
                            const key = proj.name.toLowerCase();
                            const onPypi = pypiMap.has(key);
                            const baseScore = proj.score || 0;
                            // PyPI projects get 10% bonus (multiplicative)
                            const finalScore = baseScore * (GITHUB_WEIGHT + (onPypi ? PYPI_BONUS : 0));
                            
                            return {
                                ...proj,
                                owner: owner,
                                name: projectName,
                                full_name: proj.name,
                                url: proj.html_url,
                                original_score: baseScore,
                                final_score: Math.round(finalScore),
                                on_pypi: onPypi
                            };
                        });
                        
                        scoredProjects.sort((a, b) => {
                            // Primary: sort by score (descending)
                            if (b.final_score !== a.final_score) {
                                return b.final_score - a.final_score;
                            }
                            // Secondary: PyPI projects rank higher when scores are equal
                            if (a.on_pypi !== b.on_pypi) {
                                return b.on_pypi ? 1 : -1;
                            }
                            // Tertiary: alphabetical by name
                            return a.full_name.localeCompare(b.full_name);
                        });
                        // Add global rank
                        scoredProjects.forEach((proj, idx) => {
                            proj.global_rank = idx + 1;
                        });
                        setProjects([...scoredProjects]);
                    }
                }
            } catch (error) {
                console.error("Error loading data:", error);
                setLoading(false);
            }
        };
        
        loadData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Generate search suggestions
    useEffect(() => {
        if (!searchQuery.trim()) {
            setSearchSuggestions([]);
            setShowSuggestions(false);
            return;
        }

        // Don't show suggestions if search is already active (debounced query matches)
        if (searchQuery === debouncedSearchQuery) {
            setShowSuggestions(false);
            return;
        }

        const query = searchQuery.toLowerCase().trim();
        const suggestions = [];
        
        // Get unique owners from loaded Python projects
        const ownerSet = new Set();
        projects.forEach(p => {
            const ownerLower = p.owner.toLowerCase();
            if (ownerLower.startsWith(query)) {
                ownerSet.add(p.owner);
            }
        });
        
        // Add owner suggestions
        Array.from(ownerSet).forEach(owner => {
            suggestions.push({ text: owner, type: 'owner', icon: '👤' });
        });
        
        // Add popular Python-related topics
        const popularTopics = [
            'machine-learning', 'deep-learning', 'artificial-intelligence', 'neural-networks',
            'data-science', 'data-analysis', 'visualization', 'pandas', 'numpy',
            'tensorflow', 'pytorch', 'scikit-learn', 'keras',
            'web-scraping', 'flask', 'django', 'fastapi',
            'api', 'rest', 'graphql', 'automation',
            'testing', 'pytest', 'unittest',
            'database', 'sql', 'nosql', 'mongodb', 'postgresql',
            'cli', 'command-line', 'tool', 'utility',
            'parser', 'compiler', 'interpreter'
        ];
        
        popularTopics.forEach(topic => {
            if (topic.toLowerCase().includes(query)) {
                suggestions.push({ text: topic, type: 'topic', icon: '🏷️' });
            }
        });
        
        // Sort: owners first, then topics; both alphabetically
        suggestions.sort((a, b) => {
            if (a.type !== b.type) return a.type === 'owner' ? -1 : 1;
            return a.text.localeCompare(b.text);
        });
        
        setSearchSuggestions(suggestions.slice(0, 8));
        setShowSuggestions(suggestions.length > 0);
    }, [searchQuery, debouncedSearchQuery, projects]);

    // Debounce search query - removed auto-trigger, now only on Enter
    useEffect(() => {
        if (searchTimeoutRef.current) {
            clearTimeout(searchTimeoutRef.current);
        }

        // Only clear when search is cleared
        if (!searchQuery.trim()) {
            setDebouncedSearchQuery('');
        }
    }, [searchQuery]);

    // Handle search trigger (Enter key or button)
    const triggerSearch = () => {
        setDebouncedSearchQuery(searchQuery);
        setCurrentPage(1);
        setShowSuggestions(false);
    };

    // Handle owner click - search without showing suggestions
    const handleOwnerClick = (ownerName) => {
        setShowSuggestions(false);
        setSearchSuggestions([]);
        setSearchQuery(ownerName);
        setDebouncedSearchQuery(ownerName);
        setCurrentPage(1);
    };

    // Close suggestions when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (searchWrapperRef.current && !searchWrapperRef.current.contains(event.target)) {
                setShowSuggestions(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Filter by search query
    const filteredProjects = useMemo(() => {
        if (!debouncedSearchQuery.trim()) return projects;
        
        const query = debouncedSearchQuery.toLowerCase();
        return projects.filter(p => 
            p.name.toLowerCase().includes(query) ||
            p.owner.toLowerCase().includes(query) ||
            (p.description && p.description.toLowerCase().includes(query))
        );
    }, [projects, debouncedSearchQuery]);

    // Pagination - use total from metadata when not searching
    const displayTotal = debouncedSearchQuery.trim() ? filteredProjects.length : totalProjects;
    const totalPages = Math.ceil((debouncedSearchQuery.trim() ? filteredProjects.length : totalProjects) / projectsPerPage);
    const startIndex = (currentPage - 1) * projectsPerPage;
    const currentProjects = filteredProjects.slice(startIndex, startIndex + projectsPerPage);

    const handlePageChange = (page) => {
        if (page >= 1 && page <= totalPages) {
            setCurrentPage(page);
            // Scroll to position between header and search bar
            setTimeout(() => {
                const headerElement = document.querySelector('header');
                if (headerElement) {
                    const headerBottom = headerElement.getBoundingClientRect().bottom + window.pageYOffset;
                    window.scrollTo({ top: headerBottom - 20, behavior: 'smooth' });
                }
            }, 100);
        }
    };

    return (
        <div className="container">
            <Link to="/" className="back-btn">
                ← Back
            </Link>

            <header>
                <h1>Seattle Python Source Ranker</h1>
                <p className="subtitle">
                    Top Python projects by Seattle-area developers with PyPI integration
                </p>
                {metadata && metadata.last_updated && (
                    <p className="last-updated">Last updated: {metadata.last_updated}</p>
                )}
            </header>

            {/* Search Box */}
            <div className="search-container">
                <div className="search-wrapper" ref={searchWrapperRef}>
                    <input
                        type="text"
                        className="search-input"
                        placeholder="🔍 Search projects..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onFocus={() => searchSuggestions.length > 0 && setShowSuggestions(true)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                if (selectedSuggestionIndex >= 0 && searchSuggestions.length > 0) {
                                    // Select suggestion and search
                                    const selectedText = searchSuggestions[selectedSuggestionIndex].text;
                                    setSearchQuery(selectedText);
                                    setDebouncedSearchQuery(selectedText);
                                    setShowSuggestions(false);
                                    setSelectedSuggestionIndex(-1);
                                    setCurrentPage(1);
                                } else {
                                    // Trigger search with current input
                                    triggerSearch();
                                }
                                return;
                            }
                            
                            if (!showSuggestions || searchSuggestions.length === 0) return;
                            
                            if (e.key === 'ArrowDown') {
                                e.preventDefault();
                                setSelectedSuggestionIndex(prev => 
                                    prev < searchSuggestions.length - 1 ? prev + 1 : prev
                                );
                            } else if (e.key === 'ArrowUp') {
                                e.preventDefault();
                                setSelectedSuggestionIndex(prev => prev > 0 ? prev - 1 : -1);
                            } else if (e.key === 'Escape') {
                                setShowSuggestions(false);
                                setSelectedSuggestionIndex(-1);
                            }
                        }}
                    />
                    {searchQuery && (
                        <button
                            className="clear-search-btn"
                            onClick={() => {
                                setSearchQuery('');
                                setDebouncedSearchQuery('');
                                setCurrentPage(1);
                                setShowSuggestions(false);
                            }}
                            title="Clear search"
                        >
                            ×
                        </button>
                    )}
                    
                    {/* Search Suggestions Dropdown */}
                    {showSuggestions && searchSuggestions.length > 0 && (
                        <div className="search-suggestions">
                            {searchSuggestions.map((suggestion, index) => (
                                <div
                                    key={`${suggestion.type}-${suggestion.text}`}
                                    className={`suggestion-item ${index === selectedSuggestionIndex ? 'selected' : ''}`}
                                    onMouseDown={(e) => {
                                        e.preventDefault(); // Prevent input blur
                                        const selectedText = suggestion.text;
                                        setSearchQuery(selectedText);
                                        setDebouncedSearchQuery(selectedText);
                                        setShowSuggestions(false);
                                        setSelectedSuggestionIndex(-1);
                                        setSearchSuggestions([]);
                                        setCurrentPage(1);
                                    }}
                                    onMouseEnter={() => setSelectedSuggestionIndex(index)}
                                >
                                    <span className="suggestion-icon">{suggestion.icon}</span>
                                    <span className="suggestion-text">{suggestion.text}</span>
                                    {suggestion.type === 'topic' && (
                                        <span className="suggestion-badge">Topic</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {loading ? (
                <div style={{ textAlign: "center", padding: "60px", color: "#7dd3fc" }}>
                    <div className="spinner" style={{ margin: "0 auto 12px" }}></div>
                    Loading Python projects...
                </div>
            ) : (
                <>
                    {/* Rankings Table */}
                    <div className="ranking-table">
                        <table>
                            <thead>
                                <tr>
                                    <th className="rank-col">#</th>
                                    <th className="owner-col">Owner</th>
                                    <th className="chart-col">Project Name</th>
                                    <th className="score-col">Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {currentProjects.map((project, index) => {
                                    const displayRank = project.global_rank || (startIndex + index + 1);
                                    const barWidth = project.final_score > 0
                                        ? Math.max(15, Math.min(100, (project.final_score / filteredProjects[0].final_score) * 100))
                                        : 15;

                                    return (
                                        <tr key={project.full_name}>
                                            <td className="rank-col">#{displayRank}</td>
                                            <td className="owner-col">
                                                <span
                                                    className="owner-link"
                                                    onClick={() => handleOwnerClick(project.owner)}
                                                    title={`Search for ${project.owner}`}
                                                >
                                                    {project.owner}
                                                </span>
                                            </td>
                                            <td className="chart-col">
                                                <div 
                                                    className="bar-container"
                                                    onMouseEnter={(e) => {
                                                        if (timeoutRef.current) {
                                                            clearTimeout(timeoutRef.current);
                                                        }
                                                        
                                                        // Calculate tooltip position
                                                        const container = e.currentTarget;
                                                        const rect = container.getBoundingClientRect();
                                                        const viewportHeight = window.innerHeight;
                                                        const tooltipHeight = 200;
                                                        const spaceBelow = viewportHeight - rect.bottom;
                                                        
                                                        // If not enough space below, show tooltip above
                                                        const showAbove = spaceBelow < tooltipHeight + 20;
                                                        
                                                        setTooltipPosition({
                                                            [project.full_name]: showAbove
                                                        });
                                                        setHoveredProject(project.full_name);
                                                    }}
                                                    onMouseLeave={() => {
                                                        timeoutRef.current = setTimeout(() => {
                                                            setHoveredProject(null);
                                                        }, 150);
                                                    }}
                                                >
                                                    <a
                                                        href={project.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="bar-link"
                                                    >
                                                        <div
                                                            className="bar"
                                                            style={{ width: `${barWidth}%` }}
                                                        >
                                                            <span className="project-name">
                                                                {project.name}
                                                                {project.on_pypi && (
                                                                    <span className="pypi-badge">PyPI</span>
                                                                )}
                                                            </span>
                                                        </div>
                                                    </a>
                                                    {hoveredProject === project.full_name && (
                                                        <div 
                                                            className={`tooltip ${tooltipPosition[project.full_name] ? 'tooltip-above' : ''}`}
                                                            onMouseEnter={() => {
                                                                if (timeoutRef.current) {
                                                                    clearTimeout(timeoutRef.current);
                                                                }
                                                                setHoveredProject(project.full_name);
                                                            }}
                                                            onMouseLeave={() => {
                                                                setHoveredProject(null);
                                                            }}
                                                        >
                                                            <div className="tooltip-title">{project.name}</div>
                                                            <div className="tooltip-desc">
                                                                <div style={{ marginBottom: "8px" }}>
                                                                    <strong>Language:</strong> {project.language}
                                                                </div>
                                                                {project.topics && project.topics.length > 0 && (
                                                                    <div style={{ marginBottom: "8px" }}>
                                                                        <strong>Tech Stack:</strong>{" "}
                                                                        {project.topics.slice(0, 5).join(", ")}
                                                                    </div>
                                                                )}
                                                                <div style={{ marginBottom: "8px" }}>
                                                                    <strong>Description:</strong> {project.description || "No description available"}
                                                                </div>
                                                                <div>
                                                                    ⭐ {project.stars.toLocaleString()} stars | 👁️{" "}
                                                                    {(project.watchers || 0).toLocaleString()} watchers | 🔀{" "}
                                                                    {project.forks.toLocaleString()} forks | 🐛{" "}
                                                                    {project.issues.toLocaleString()} issues
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="score-col">{project.final_score.toLocaleString()}</td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>

                    {/* Page Info */}
                    <div
                        style={{
                            textAlign: "center",
                            margin: "20px 0 15px",
                            color: "#999",
                            fontSize: "0.95em"
                        }}
                    >
                        {!debouncedSearchQuery.trim() ? (
                            <>
                                Showing {startIndex + 1}-{Math.min(startIndex + projectsPerPage, filteredProjects.length)}{" "}
                                of {displayTotal.toLocaleString()} projects
                            </>
                        ) : (
                            <>
                                Showing {currentProjects.length > 0 ? startIndex + 1 : 0}-
                                {currentProjects.length > 0 ? startIndex + currentProjects.length : 0}{" "}
                                of {filteredProjects.length.toLocaleString()} matches
                            </>
                        )}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="pagination-container">
                            <button
                                className="pagination-btn pagination-edge"
                                onClick={() => {
                                    setCurrentPage(1);
                                    setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 100);
                                }}
                                disabled={currentPage === 1}
                            >
                                «
                            </button>
                            <button
                                className="pagination-btn"
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage === 1}
                            >
                                ‹
                            </button>

                            <div className="page-input-wrapper">
                                <input
                                    type="number"
                                    className="page-input"
                                    value={pageInput !== null ? pageInput : currentPage}
                                    onChange={(e) => setPageInput(e.target.value)}
                                    onFocus={(e) => {
                                        if (pageInput === null) {
                                            setPageInput(currentPage.toString());
                                            setTimeout(() => e.target.select(), 0);
                                        }
                                    }}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            e.preventDefault();
                                            const pageNum = parseInt(pageInput);
                                            if (pageNum >= 1 && pageNum <= totalPages) {
                                                handlePageChange(pageNum);
                                                setPageInput(null);
                                            }
                                            e.target.blur();
                                        } else if (e.key === 'Escape') {
                                            setPageInput(null);
                                            e.target.blur();
                                        } else if (e.key === 'ArrowUp') {
                                            e.preventDefault();
                                            const current = parseInt(pageInput) || currentPage;
                                            const newPage = Math.min(totalPages, current + 1);
                                            setPageInput(newPage.toString());
                                        } else if (e.key === 'ArrowDown') {
                                            e.preventDefault();
                                            const current = parseInt(pageInput) || currentPage;
                                            const newPage = Math.max(1, current - 1);
                                            setPageInput(newPage.toString());
                                        }
                                    }}
                                    onBlur={() => {
                                        setPageInput(null);
                                    }}
                                    min="1"
                                    max={totalPages}
                                />
                                <span className="page-total">/ {totalPages}</span>
                            </div>

                            <button
                                className="pagination-btn"
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage === totalPages}
                            >
                                ›
                            </button>
                            <button
                                className="pagination-btn pagination-edge"
                                onClick={() => handlePageChange(totalPages)}
                                disabled={currentPage === totalPages}
                            >
                                »
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
