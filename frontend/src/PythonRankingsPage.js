// src/PythonProjectsPage.js
import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { Link, useSearchParams } from "react-router-dom";

// Scoring configuration - Multiplicative bonus approach
const GITHUB_WEIGHT = 1.0;       // 100% of base score
const PYPI_BONUS = 0.1;          // +10% multiplier for PyPI projects

// Current formula: finalScore = baseScore * (1.0 + 0.1) = baseScore * 1.1
// Future: Can change to weighted average by using separate weights for GitHub/PyPI components

export default function PythonRankingsPage() {
    const [searchParams, setSearchParams] = useSearchParams();
    
    // Initialize state from URL parameters
    const [currentPage, setCurrentPage] = useState(() => {
        const pageParam = searchParams.get('page');
        return pageParam ? parseInt(pageParam, 10) : 1;
    });
    const [activeOwner, setActiveOwner] = useState(() => searchParams.get('search') || null);
    const [searchQuery, setSearchQuery] = useState(() => searchParams.get('search') || '');
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState(() => searchParams.get('search') || '');
    
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(false);
    const [metadata, setMetadata] = useState(null);
    const [totalProjects, setTotalProjects] = useState(0);
    const [tooltipPosition, setTooltipPosition] = useState({});
    const [hoveredProject, setHoveredProject] = useState(null);
    const [searchSuggestions, setSearchSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
    const [pageInput, setPageInput] = useState(null);
    const [updatingRows, setUpdatingRows] = useState(false);
    const [pageCache, setPageCache] = useState({}); // Cache loaded pages
    const [pypiMap, setPypiMap] = useState(null); // PyPI lookup map
    const [tableFlash, setTableFlash] = useState(false);
    
    const pageBeforeSearchRef = useRef(1);
    const timeoutRef = useRef(null);
    const searchTimeoutRef = useRef(null);
    const searchWrapperRef = useRef(null);
    const skipScanAnimationRef = useRef(searchParams.get('search') !== null);
    const forceScanAnimationRef = useRef(false);
    const tableFlashTimeoutRef = useRef(null);
    const previousFiltersRef = useRef({ search: debouncedSearchQuery });
    const isInitialLoadRef = useRef(true);
    const projectsPerPage = 50;

    // Use refs to track current values without causing re-renders
    const currentPageRef = useRef(currentPage);
    const debouncedSearchQueryRef = useRef(debouncedSearchQuery);
    
    useEffect(() => {
        currentPageRef.current = currentPage;
    }, [currentPage]);
    
    useEffect(() => {
        debouncedSearchQueryRef.current = debouncedSearchQuery;
    }, [debouncedSearchQuery]);

    // Load metadata and PyPI data once
    useEffect(() => {
        const loadMetadata = async () => {
            try {
                // Load metadata
                const metadataRes = await fetch(`${process.env.PUBLIC_URL}/metadata.json`);
                const metadataData = await metadataRes.json();
                setMetadata(metadataData);
                
                // Set total projects count from metadata
                const pythonTotal = metadataData.languages.Python?.total || 0;
                setTotalProjects(pythonTotal);
                
                // Load PyPI data and build lookup map
                try {
                    const pypiRes = await fetch(`${process.env.PUBLIC_URL}/data/seattle_pypi_projects.json`);
                    const pypiData = await pypiRes.json();
                    const map = new Map();
                    pypiData.projects.forEach(p => {
                        const key = `${p.owner}/${p.name}`.toLowerCase();
                        map.set(key, p);
                    });
                    setPypiMap(map);
                } catch (error) {
                    console.warn("PyPI data not available:", error);
                    setPypiMap(new Map());
                }
            } catch (error) {
                console.error("Failed to load metadata:", error);
            }
        };
        
        loadMetadata();
    }, []);
    
    // Save scroll position before unload (for F5 refresh)
    useEffect(() => {
        const handleBeforeUnload = () => {
            sessionStorage.setItem('pythonScrollPosition', window.pageYOffset.toString());
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, []);
    
    // Mark initial load as complete and restore scroll position after first data load
    useEffect(() => {
        if (projects.length > 0 && isInitialLoadRef.current) {
            isInitialLoadRef.current = false;
            
            // Restore scroll position with smooth animation after a short delay to ensure content is rendered
            const savedScrollPosition = sessionStorage.getItem('pythonScrollPosition');
            if (savedScrollPosition) {
                setTimeout(() => {
                    window.scrollTo({ top: parseInt(savedScrollPosition, 10), behavior: 'smooth' });
                    sessionStorage.removeItem('pythonScrollPosition');
                }, 100);
            }
        }
    }, [projects]);

    // Sync state when URL changes (browser back/forward)
    useEffect(() => {
        const searchParam = searchParams.get('search');
        const pageParam = searchParams.get('page');
        
        // Only update if values actually changed (to avoid infinite loops)
        if (searchParam !== debouncedSearchQueryRef.current) {
            const newSearch = searchParam || '';
            setSearchQuery(newSearch);
            setDebouncedSearchQuery(newSearch);
            setActiveOwner(newSearch || null);
            setShowSuggestions(false);
            if (newSearch) {
                skipScanAnimationRef.current = true;
            }
        }
        
        // Update page number
        if (pageParam) {
            const page = parseInt(pageParam, 10);
            if (!isNaN(page) && page > 0 && page !== currentPageRef.current) {
                setCurrentPage(page);
            }
        }
    }, [searchParams]);

    // Load current page data (simple on-demand loading)
    useEffect(() => {
        if (!metadata || !pypiMap || debouncedSearchQuery.trim()) return;
        
        const loadPageData = async () => {
            const cacheKey = `page_${currentPage}`;
            
            // Reset totalProjects to full count when not searching
            const pythonTotal = metadata.languages.Python?.total || 0;
            setTotalProjects(pythonTotal);
            
            // Check cache first
            if (pageCache[cacheKey]) {
                setProjects(pageCache[cacheKey]);
                setLoading(false);
                
                // Skip animation on initial load
                if (!isInitialLoadRef.current) {
                    // Trigger animation based on flags
                    if (forceScanAnimationRef.current) {
                        // Force scan animation (from clear button for general search)
                        if (tableFlashTimeoutRef.current) {
                            clearTimeout(tableFlashTimeoutRef.current);
                        }
                        setTableFlash(false);
                        // Double requestAnimationFrame to ensure DOM update
                        requestAnimationFrame(() => {
                            requestAnimationFrame(() => {
                                setTableFlash(true);
                                tableFlashTimeoutRef.current = setTimeout(() => {
                                    setTableFlash(false);
                                    tableFlashTimeoutRef.current = null;
                                }, 2000);
                            });
                        });
                    } else if (skipScanAnimationRef.current) {
                        // Use row animation (from owner clear)
                        setUpdatingRows(true);
                        setTimeout(() => setUpdatingRows(false), 600);
                    } else {
                        // Normal cache hit, simple flash
                        setTableFlash(true);
                        setTimeout(() => setTableFlash(false), 2000);
                    }
                }
                
                // Reset flags
                skipScanAnimationRef.current = false;
                forceScanAnimationRef.current = false;
                isInitialLoadRef.current = false;
                return;
            }
            
            // Set loading state if not skipping animation
            if (!skipScanAnimationRef.current) {
                setLoading(true);
            }
            
            try {
                // Load single page
                const response = await fetch(`${process.env.PUBLIC_URL}/pages/python/page_${currentPage}.json`);
                const pageData = await response.json();
                
                // Process with PyPI bonus
                const scoredProjects = pageData.map((proj, idx) => {
                    const [owner, projectName] = proj.name.split('/');
                    const key = proj.name.toLowerCase();
                    const onPypi = pypiMap.has(key);
                    const baseScore = proj.score || 0;
                    const finalScore = baseScore * (GITHUB_WEIGHT + (onPypi ? PYPI_BONUS : 0));
                    
                    return {
                        ...proj,
                        owner: owner,
                        name: projectName,
                        full_name: proj.name,
                        url: proj.html_url,
                        original_score: baseScore,
                        final_score: Math.round(finalScore),
                        on_pypi: onPypi,
                        python_rank: (currentPage - 1) * 50 + idx + 1  // Python-specific rank
                    };
                });
                
                setProjects(scoredProjects);
                setPageCache(prev => ({ ...prev, [cacheKey]: scoredProjects }));
            } catch (error) {
                console.error(`Failed to load page ${currentPage}:`, error);
                setProjects([]);
            }
            
            // Close loading state after data is ready
            setLoading(false);
            
            // Check if filters actually changed
            const filtersChanged = previousFiltersRef.current.search !== debouncedSearchQuery;
            
            // THEN trigger animation after data is ready (skip on initial load)
            if (!isInitialLoadRef.current) {
                if ((filtersChanged && !skipScanAnimationRef.current) || forceScanAnimationRef.current) {
                    // Clear any existing timeout
                    if (tableFlashTimeoutRef.current) {
                        clearTimeout(tableFlashTimeoutRef.current);
                    }
                    // Force restart animation
                    setTableFlash(false);
                    // Double requestAnimationFrame to ensure DOM update
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            setTableFlash(true);
                            tableFlashTimeoutRef.current = setTimeout(() => {
                                setTableFlash(false);
                                tableFlashTimeoutRef.current = null;
                            }, 2000);
                        });
                    });
                } else if (filtersChanged && skipScanAnimationRef.current) {
                    // Use row animation for owner searches
                    setUpdatingRows(true);
                    setTimeout(() => setUpdatingRows(false), 600);
                }
            }
            
            // Update previous filters
            previousFiltersRef.current = { search: debouncedSearchQuery };
            
            // Reset the flags after checking
            skipScanAnimationRef.current = false;
            forceScanAnimationRef.current = false;
            isInitialLoadRef.current = false;
        };
        
        loadPageData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [metadata, pypiMap, currentPage, debouncedSearchQuery]);

    // Search functionality - use owner index for owner searches, load all for other searches
    useEffect(() => {
        if (!metadata || !pypiMap || !debouncedSearchQuery.trim()) {
            return;
        }
        
        const loadSearchData = async () => {
            // Don't show loading on initial page load (F5 refresh)
            if (!isInitialLoadRef.current) {
                // Only show loading for general searches that require scanning all pages
                const shouldShowLoading = !skipScanAnimationRef.current && !activeOwner;
                if (shouldShowLoading) {
                    setLoading(true);
                }
            }
            
            try {
                const query = debouncedSearchQuery.toLowerCase();
                
                // If searching for a specific owner (activeOwner set), use owner index
                if (activeOwner) {
                    const firstChar = activeOwner[0].toLowerCase();
                    const indexChar = /[a-z0-9]/.test(firstChar) ? firstChar : 'other';
                    
                    try {
                        const response = await fetch(`${process.env.PUBLIC_URL}/python_owner_index/${indexChar}.json`);
                        const ownerData = await response.json();
                        const projects = ownerData[activeOwner] || [];
                        
                        // Projects from index already have final_score and on_pypi
                        const formatted = projects.map(p => ({
                            ...p,
                            name: p.name.split('/')[1],
                            full_name: p.name,
                            url: p.html_url,
                            original_score: p.score
                            // Keep python_rank from index - don't reassign
                        }));
                        
                        setProjects(formatted);
                        setTotalProjects(formatted.length);
                    } catch (error) {
                        console.error(`Failed to load owner index for ${activeOwner}:`, error);
                        setProjects([]);
                    }
                } else {
                    // For general search (project name, description), load all pages
                    const pythonPages = metadata.languages.Python?.pages || 0;
                    const allPromises = [];
                    
                    // Load all pages for search
                    for (let i = 1; i <= pythonPages; i++) {
                        allPromises.push(
                            fetch(`${process.env.PUBLIC_URL}/pages/python/page_${i}.json`)
                                .then(res => res.json())
                                .catch(() => [])
                        );
                    }
                    
                    const allPages = await Promise.all(allPromises);
                    const allProjects = [];
                    allPages.forEach(pageData => {
                        allProjects.push(...pageData);
                    });
                    
                    // Process and filter
                    const filtered = allProjects
                        .map(proj => {
                            const [owner, projectName] = proj.name.split('/');
                            const key = proj.name.toLowerCase();
                            const onPypi = pypiMap.has(key);
                            const baseScore = proj.score || 0;
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
                                // Keep python_rank from page data - don't reassign
                            };
                        })
                        .filter(p => {
                            // Fuzzy search for project name, owner, or description
                            return p.name.toLowerCase().includes(query) ||
                                   p.owner.toLowerCase().includes(query) ||
                                   (p.description && p.description.toLowerCase().includes(query));
                        });
                    
                    setProjects(filtered);
                    setTotalProjects(filtered.length);
                }
            } catch (error) {
                console.error("Failed to load search data:", error);
                setProjects([]);
            }
            
            // Always close loading state after data is loaded
            setLoading(false);
            
            // Trigger animation after search data is loaded (skip on initial load)
            if (!isInitialLoadRef.current) {
                if (skipScanAnimationRef.current) {
                    // Use row animation for owner searches
                    setUpdatingRows(true);
                    setTimeout(() => setUpdatingRows(false), 600);
                    skipScanAnimationRef.current = false;
                } else {
                    // Use scan animation for general searches
                    if (tableFlashTimeoutRef.current) {
                        clearTimeout(tableFlashTimeoutRef.current);
                    }
                    setTableFlash(false);
                    requestAnimationFrame(() => {
                        setTableFlash(true);
                        tableFlashTimeoutRef.current = setTimeout(() => {
                            setTableFlash(false);
                            tableFlashTimeoutRef.current = null;
                        }, 2000);
                    });
                }
            } else {
                // Reset flag on initial load without animation
                skipScanAnimationRef.current = false;
                isInitialLoadRef.current = false;
            }
        };
        
        loadSearchData();
    }, [metadata, pypiMap, debouncedSearchQuery, activeOwner]);

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
        const firstChar = query[0] && query[0].match(/[a-z0-9]/) ? query[0] : 'other';
        
        // Load Python owner index and generate suggestions
        const loadAndGenerateSuggestions = async () => {
            const suggestions = [];
            
            // Load owner suggestions from python_owner_index
            try {
                const response = await fetch(`${process.env.PUBLIC_URL}/python_owner_index/${firstChar}.json`);
                if (response.ok) {
                    const data = await response.json();
                    const owners = Object.keys(data);
                    owners.forEach(owner => {
                        if (owner.toLowerCase().includes(query)) {
                            suggestions.push({ text: owner, type: 'owner', icon: '👤' });
                        }
                    });
                }
            } catch (err) {
                console.log(`Failed to load Python owner suggestions for '${firstChar}'`);
            }
            
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
                'parser', 'compiler', 'interpreter', 'nlp', 'computer-vision',
                'asyncio', 'multiprocessing', 'websocket', 'bot', 'scraper'
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
            
            // Limit: max 8 owners, 4 topics (no languages, so more space than Overall's 4+3+2)
            const limitedSuggestions = [];
            const typeCounts = { 'owner': 0, 'topic': 0 };
            const typeMaxCounts = { 'owner': 8, 'topic': 4 };
            
            for (const suggestion of suggestions) {
                if (typeCounts[suggestion.type] < typeMaxCounts[suggestion.type]) {
                    limitedSuggestions.push(suggestion);
                    typeCounts[suggestion.type]++;
                }
                if (limitedSuggestions.length >= 12) break;
            }
            
            setSearchSuggestions(limitedSuggestions);
            setShowSuggestions(limitedSuggestions.length > 0);
        };
        
        loadAndGenerateSuggestions();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchQuery, debouncedSearchQuery]);

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
        // Update URL with search
        const newParams = new URLSearchParams(searchParams);
        if (searchQuery.trim()) {
            newParams.set('search', searchQuery);
        } else {
            newParams.delete('search');
        }
        newParams.set('page', '1');
        setSearchParams(newParams);
    };

    // Helper function to update page in URL
    const updatePage = (newPage) => {
        setCurrentPage(newPage);
        const newParams = new URLSearchParams(searchParams);
        newParams.set('page', newPage.toString());
        setSearchParams(newParams);
    };

    // Handle owner click - search without showing suggestions, click again to clear
    const handleOwnerClick = (ownerName) => {
        setShowSuggestions(false);
        setSearchSuggestions([]);
        
        // ALWAYS skip scan animation for owner clicks - use row animation only
        skipScanAnimationRef.current = true;
        setTableFlash(false);
        
        // If clicking the same owner, clear search and return to previous page
        if (activeOwner === ownerName) {
            setSearchQuery('');
            setDebouncedSearchQuery('');
            setActiveOwner(null);
            // Return to the page we were on before the search
            const returnPage = pageBeforeSearchRef.current;
            setCurrentPage(returnPage);
            const newParams = new URLSearchParams(searchParams);
            newParams.delete('search');
            newParams.set('page', returnPage.toString());
            setSearchParams(newParams);
        } else {
            // Remember current page before starting new owner search
            pageBeforeSearchRef.current = currentPage;
            // New owner search - reset to page 1
            setSearchQuery(ownerName);
            setDebouncedSearchQuery(ownerName);
            setActiveOwner(ownerName);
            setCurrentPage(1);
            // Update URL with search parameter
            const newParams = new URLSearchParams(searchParams);
            newParams.set('search', ownerName);
            newParams.set('page', '1');
            setSearchParams(newParams);
        }
        
        // Scroll to position between header and search bar after data loads
        setTimeout(() => {
            const headerElement = document.querySelector('header');
            if (headerElement) {
                const headerBottom = headerElement.getBoundingClientRect().bottom + window.pageYOffset;
                // Use requestAnimationFrame for smoother scroll
                requestAnimationFrame(() => {
                    window.scrollTo({ top: headerBottom - 20, behavior: 'smooth' });
                });
            }
        }, 500);
        
        // Trigger table update animation after a tiny delay to let data prepare
        setTimeout(() => {
            setUpdatingRows(true);
            setTimeout(() => setUpdatingRows(false), 600);
        }, 50);
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

    // Pagination - projects are already filtered by search useEffect
    const displayTotal = debouncedSearchQuery.trim() ? projects.length : totalProjects;
    const totalPages = Math.ceil(displayTotal / projectsPerPage);
    const startIndex = (currentPage - 1) * projectsPerPage;
    const currentProjects = debouncedSearchQuery.trim() 
        ? projects.slice(startIndex, startIndex + projectsPerPage)
        : projects; // For non-search, projects already contains one page

    const handlePageChange = (page) => {
        if (page >= 1 && page <= totalPages) {
            updatePage(page);
            // Scroll to top if going to page 1, otherwise scroll to header bottom
            setTimeout(() => {
                if (page === 1) {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                    const headerElement = document.querySelector('header');
                    if (headerElement) {
                        const headerBottom = headerElement.getBoundingClientRect().bottom + window.pageYOffset;
                        window.scrollTo({ top: headerBottom - 20, behavior: 'smooth' });
                    }
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
                                    const suggestion = searchSuggestions[selectedSuggestionIndex];
                                    const selectedText = suggestion.text;
                                    
                                    // If it's an owner suggestion, skip scan animation
                                    if (suggestion.type === 'owner') {
                                        skipScanAnimationRef.current = true;
                                        setTableFlash(false);
                                        setActiveOwner(selectedText);
                                    }
                                    
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
                                // Check if this is an owner search before clearing
                                const isOwnerSearch = activeOwner !== null;
                                
                                if (isOwnerSearch) {
                                    // For owner search, skip scan animation (use row animation in loadPageData)
                                    skipScanAnimationRef.current = true;
                                    forceScanAnimationRef.current = false;
                                } else {
                                    // For general search, force scan animation in loadPageData
                                    skipScanAnimationRef.current = false;
                                    forceScanAnimationRef.current = true;
                                }
                                
                                setSearchQuery('');
                                setDebouncedSearchQuery('');
                                // Return to the page we were on before the search
                                const returnPage = pageBeforeSearchRef.current;
                                setCurrentPage(returnPage);
                                setShowSuggestions(false);
                                setActiveOwner(null);
                                // Clear URL parameters
                                const newParams = new URLSearchParams(searchParams);
                                newParams.delete('search');
                                newParams.set('page', returnPage.toString());
                                setSearchParams(newParams);
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
                                        
                                        // If it's an owner suggestion, skip scan animation
                                        if (suggestion.type === 'owner') {
                                            skipScanAnimationRef.current = true;
                                            setTableFlash(false);
                                            setActiveOwner(selectedText);
                                        }
                                        
                                        setSearchQuery(selectedText);
                                        setDebouncedSearchQuery(selectedText);
                                        setShowSuggestions(false);
                                        setSelectedSuggestionIndex(-1);
                                        setSearchSuggestions([]);
                                        setCurrentPage(1);
                                    }}
                                    onMouseEnter={() => setSelectedSuggestionIndex(index)}
                                >
                                    <div className="suggestion-left">
                                        <span className="suggestion-icon">{suggestion.icon}</span>
                                        <span className="suggestion-text">{suggestion.text}</span>
                                    </div>
                                    {suggestion.type === 'owner' && (
                                        <span className="suggestion-badge">User</span>
                                    )}
                                    {suggestion.type === 'topic' && (
                                        <span className="suggestion-badge">Topic</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                {loading && (
                    <div className="search-hint loading-indicator">
                        <span className="spinner"></span>
                        <span>Loading...</span>
                    </div>
                )}
            </div>

            {/* Rankings Table */}
            <div className={`ranking-table ${tableFlash ? 'table-flash' : ''}`}>
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
                                    const displayRank = project.python_rank || (startIndex + index + 1);
                                    const barWidth = project.final_score > 0
                                        ? Math.max(15, Math.min(100, (project.final_score / currentProjects[0]?.final_score) * 100))
                                        : 50

                                    return (
                                        <tr 
                                            key={project.full_name} 
                                            className={updatingRows ? 'row-updating' : ''}
                                            style={updatingRows ? { animationDelay: `${index * 0.03}s` } : {}}
                                        >
                                            <td className="rank-col">#{displayRank}</td>
                                            <td className="owner-col">
                                                <span
                                                    className={`owner-link ${activeOwner === project.owner ? 'owner-active' : ''}`}
                                                    onClick={() => handleOwnerClick(project.owner)}
                                                    title={activeOwner === project.owner ? `Click to clear search` : `Search for ${project.owner}`}
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
                                Showing {startIndex + 1}-{Math.min(startIndex + projectsPerPage, projects.length)}{" "}
                                of {displayTotal.toLocaleString()} projects
                            </>
                        ) : (
                            <>
                                Showing {currentProjects.length > 0 ? startIndex + 1 : 0}-
                                {currentProjects.length > 0 ? startIndex + currentProjects.length : 0}{" "}
                                of {projects.length.toLocaleString()} matches
                            </>
                        )}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="pagination-container">
                            <button
                                className="pagination-btn pagination-edge"
                                onClick={() => {
                                    updatePage(1);
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
        </div>
    );
}
