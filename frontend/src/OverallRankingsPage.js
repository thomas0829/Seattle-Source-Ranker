// src/RankingsPage.js
import React, { useEffect, useState, useRef } from "react";
import "./App.css";
import { Link } from "react-router-dom";

export default function OverallRankingsPage() {
    const [metadata, setMetadata] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [repos, setRepos] = useState([]);
    const [hoveredRepo, setHoveredRepo] = useState(null);
    const [maxScore, setMaxScore] = useState(1);
    const [repoDetails, setRepoDetails] = useState({});
    const [languages, setLanguages] = useState([]);
    const [selectedLanguages, setSelectedLanguages] = useState([]);
    const [showAll, setShowAll] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [pageCache, setPageCache] = useState({});
    const [top10000Cache, setTop10000Cache] = useState(null); // Cache for top 10000 projects
    const timeoutRef = useRef(null);
    const searchTimeoutRef = useRef(null);
    const [pageInput, setPageInput] = useState(null);
    const [searchMatchCounts, setSearchMatchCounts] = useState({});
    const [ownerIndexCache, setOwnerIndexCache] = useState({});
    const [showFilters, setShowFilters] = useState(false);
    const [searchSuggestions, setSearchSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
    const searchWrapperRef = useRef(null);
    const [tooltipPosition, setTooltipPosition] = useState({});

    const [isScrolling, setIsScrolling] = useState(false);
    const scrollTimeoutRef = useRef(null);

    // Load metadata
    useEffect(() => {
        fetch(`${process.env.PUBLIC_URL}/metadata.json`)
            .then((res) => res.json())
            .then((data) => {
                setMetadata(data);
                const langs = Object.keys(data.languages)
                    .filter((lang) => lang !== "Other")
                    .sort((a, b) => data.languages[b].total - data.languages[a].total);
                setLanguages(langs);
            })
            .catch((err) => console.error("❌ Failed to load metadata:", err));
    }, []);

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
        
        // Load the index for this character if not already loaded
        const loadAndGenerateSuggestions = async () => {
            const suggestions = [];
            
            // Try to load owner index for this character
            if (!ownerIndexCache[firstChar]) {
                try {
                    const response = await fetch(`${process.env.PUBLIC_URL}/owner_index/${firstChar}.json`);
                    if (response.ok) {
                        const data = await response.json();
                        setOwnerIndexCache(prev => ({ ...prev, [firstChar]: data }));
                        
                        // Generate owner suggestions from the newly loaded data
                        const owners = Object.keys(data);
                        owners.forEach(owner => {
                            if (owner.toLowerCase().includes(query)) {
                                suggestions.push({ text: owner, type: 'owner', icon: '👤' });
                            }
                        });
                    }
                } catch (err) {
                    console.log(`Failed to load suggestions for '${firstChar}'`);
                }
            } else {
                // Use cached owner data
                const owners = Object.keys(ownerIndexCache[firstChar]);
                owners.forEach(owner => {
                    if (owner.toLowerCase().includes(query)) {
                        suggestions.push({ text: owner, type: 'owner', icon: '👤' });
                    }
                });
            }
            
            // Add popular topic suggestions
            const popularTopics = [
                'machine-learning', 'deep-learning', 'artificial-intelligence', 'neural-networks',
                'react', 'vue', 'angular', 'typescript', 'javascript',
                'python', 'data-science', 'data-analysis', 'visualization',
                'api', 'rest', 'graphql', 'docker', 'kubernetes',
                'blockchain', 'cryptocurrency', 'web3',
                'database', 'sql', 'nosql', 'mongodb', 'postgresql',
                'testing', 'automation', 'ci-cd', 'devops',
                'security', 'authentication', 'encryption'
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
        };
        
        loadAndGenerateSuggestions();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchQuery, ownerIndexCache]);

    // Click outside to close suggestions
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (searchWrapperRef.current && !searchWrapperRef.current.contains(event.target)) {
                setShowSuggestions(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Debounce search query - removed auto-trigger, now only on Enter
    useEffect(() => {
        if (searchTimeoutRef.current) {
            clearTimeout(searchTimeoutRef.current);
        }

        // Only clear match counts when search is cleared
        if (!searchQuery.trim()) {
            setDebouncedSearchQuery('');
            setSearchMatchCounts({});
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

    // Load page data based on selected languages and search
    useEffect(() => {
        if (!metadata) return;

        const loadData = async () => {
            // If showAll is true (no specific languages selected), show mixed content
            if (showAll && !debouncedSearchQuery.trim()) {
                await loadMixedPage();
            } else if (debouncedSearchQuery.trim()) {
                await loadSearchResults();
            } else {
                await loadSelectedLanguages();
            }
        };

        loadData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [metadata, selectedLanguages, showAll, debouncedSearchQuery, currentPage]);

    // Scroll to position between header and search bar when page changes
    useEffect(() => {
        // Skip scroll on initial page load (page 1)
        if (currentPage === 1) return;
        
        // Use setTimeout to ensure DOM is ready
        const timer = setTimeout(() => {
            const headerElement = document.querySelector('header');
            if (headerElement) {
                const headerBottom = headerElement.getBoundingClientRect().bottom + window.pageYOffset;
                window.scrollTo({ top: headerBottom - 20, behavior: 'smooth' });
            }
        }, 100);
        return () => clearTimeout(timer);
    }, [currentPage]);

    // Load mixed page (all languages, lazy loading)
    const loadMixedPage = async () => {
        const cacheKey = `mixed_${currentPage}`;
        if (pageCache[cacheKey]) {
            setRepos(pageCache[cacheKey]);
            return;
        }

        setIsLoading(true);
        const pageSize = 50;

        // If we already have the top 10000 cached, use it directly
        if (top10000Cache) {
            const startIndex = (currentPage - 1) * pageSize;
            const pageRepos = top10000Cache.slice(startIndex, startIndex + pageSize);
            setRepos(pageRepos);
            setPageCache((prev) => ({ ...prev, [cacheKey]: pageRepos }));
            setIsLoading(false);
            return;
        }

        // For first page: load minimal data (just 2 pages per language)
        // For other pages: load more progressively
        const allReposForLoad = [];
        const langsToLoad = showAll ? [...languages, 'Other'] : languages;
        
        // Optimize for first page - load minimal data
        const quickLoadPages = currentPage === 1 ? 2 : Math.max(3, Math.ceil((currentPage * pageSize + 100) / langsToLoad.length / 50));
        
        // Load pages in parallel for better performance
        const loadPromises = langsToLoad.map(async (lang) => {
            const langRepos = [];
            for (let page = 1; page <= quickLoadPages; page++) {
                const langPath = lang.toLowerCase().replace(/\+/g, "plus");
                const pageUrl = `${process.env.PUBLIC_URL}/pages/${langPath}/page_${page}.json`;

                try {
                    const response = await fetch(pageUrl);
                    const pageData = await response.json();
                    const reposWithLang = pageData.map((repo) => ({
                        ...repo,
                        language: lang
                    }));
                    langRepos.push(...reposWithLang);
                } catch (err) {
                    console.error(`Failed to load ${lang} page ${page}:`, err);
                }
            }
            return langRepos;
        });

        // Wait for all languages to load in parallel
        const results = await Promise.all(loadPromises);
        results.forEach(langRepos => allReposForLoad.push(...langRepos));

        // Sort and display current page immediately
        allReposForLoad.sort((a, b) => (a.global_rank || 999999) - (b.global_rank || 999999));
        const startIndex = (currentPage - 1) * pageSize;
        const pageRepos = allReposForLoad.slice(startIndex, startIndex + pageSize);
        
        setRepos(pageRepos);
        setPageCache((prev) => ({ ...prev, [cacheKey]: pageRepos }));
        
        if (pageRepos.length > 0) {
            const pageMax = Math.max(...pageRepos.map((r) => r.score));
            if (pageMax > maxScore) setMaxScore(pageMax);
        }
        
        setIsLoading(false);

        // Load remaining data in background for future pages (only if on first page)
        if (currentPage === 1 && !isScrolling) {
            setTimeout(() => {
                loadFullTop10000();
            }, 100);
        }
    };

    // Load full top 10000 dataset
    const loadFullTop10000 = async () => {
        if (top10000Cache) return top10000Cache; // Already loaded
        if (isScrolling) return; // Pause loading while scrolling

        const allReposForLoad = [];
        const langsToLoad = showAll ? [...languages, 'Other'] : languages;
        const maxPagesToLoadPerLang = 100;

        for (const lang of langsToLoad) {
            const totalPagesForLang = metadata.languages[lang].pages;
            const pagesToLoad = Math.min(maxPagesToLoadPerLang, totalPagesForLang);

            for (let page = 1; page <= pagesToLoad; page++) {
                const langPath = lang.toLowerCase().replace(/\+/g, "plus");
                const pageUrl = `${process.env.PUBLIC_URL}/pages/${langPath}/page_${page}.json`;

                try {
                    const response = await fetch(pageUrl);
                    const pageData = await response.json();
                    const reposWithLang = pageData.map((repo) => ({
                        ...repo,
                        language: lang
                    }));
                    allReposForLoad.push(...reposWithLang);
                } catch (err) {
                    console.error(`Failed to load ${lang} page ${page}:`, err);
                }
            }
        }

        // Sort by global_rank to get the true top 10000
        allReposForLoad.sort((a, b) => (a.global_rank || 999999) - (b.global_rank || 999999));
        
        // Take only projects with global_rank <= 10000
        const top10000 = allReposForLoad.filter(repo => repo.global_rank && repo.global_rank <= 10000);
        
        // Cache the top 10000 for future use
        setTop10000Cache(top10000);
        return top10000;
    };

    // Load selected languages (need to load enough pages to get to current page)
    const loadSelectedLanguages = async () => {
        const cacheKey = `langs_${selectedLanguages.join(",")}_${currentPage}`;
        if (pageCache[cacheKey]) {
            setRepos(pageCache[cacheKey]);
            return;
        }

        setIsLoading(true);
        const pageSize = 50;
        const MAX_PROJECTS = 10000;
        const allReposForLoad = [];

        // For selected languages, load pages in order (already sorted by score within each language)
        // We want the top projects from each language, not by global rank
        const maxPagesToLoad = Math.ceil(MAX_PROJECTS / pageSize);

        for (const lang of selectedLanguages) {
            const totalPagesForLang = metadata.languages[lang].pages;
            const pagesToLoad = Math.min(maxPagesToLoad, totalPagesForLang);

            for (let page = 1; page <= pagesToLoad; page++) {
                const langPath = lang.toLowerCase().replace(/\+/g, "plus");
                const pageUrl = `${process.env.PUBLIC_URL}/pages/${langPath}/page_${page}.json`;

                try {
                    const response = await fetch(pageUrl);
                    const pageData = await response.json();
                    const reposWithLang = pageData.map((repo) => ({
                        ...repo,
                        language: lang
                    }));
                    allReposForLoad.push(...reposWithLang);
                } catch (err) {
                    console.error(`Failed to load ${lang} page ${page}:`, err);
                }
            }
        }

        // Sort by score (for selected languages, we show top scored projects, not global rank)
        allReposForLoad.sort((a, b) => b.score - a.score);
        
        // Limit to first 10000 projects
        const limitedRepos = allReposForLoad.slice(0, MAX_PROJECTS);
        
        const startIndex = (currentPage - 1) * pageSize;
        const pageRepos = limitedRepos.slice(startIndex, startIndex + pageSize);

        setRepos(pageRepos);
        setPageCache((prev) => ({ ...prev, [cacheKey]: pageRepos }));

        if (pageRepos.length > 0) {
            const pageMax = Math.max(...pageRepos.map((r) => r.score));
            if (pageMax > maxScore) setMaxScore(pageMax);
        }

        setIsLoading(false);
    };

    // Load search results (use owner index for fast exact owner searches)
    const loadSearchResults = async () => {
        setIsLoading(true);
        const query = debouncedSearchQuery.toLowerCase().trim();
        
        // Try to load owner index for exact match
        const firstChar = query[0] && query[0].match(/[a-z0-9]/) ? query[0] : 'other';
        
        // Load owner index if not cached
        let indexData = ownerIndexCache[firstChar];
        if (!indexData) {
            try {
                console.log(`📥 Loading owner index: ${firstChar}.json`);
                const response = await fetch(`${process.env.PUBLIC_URL}/owner_index/${firstChar}.json`);
                if (response.ok) {
                    indexData = await response.json();
                    setOwnerIndexCache(prev => ({ ...prev, [firstChar]: indexData }));
                    console.log(`✅ Loaded owner index for '${firstChar}'`, Object.keys(indexData).length, 'owners');
                } else {
                    console.log(`❌ Failed to load owner index for '${firstChar}': ${response.status}`);
                }
            } catch (err) {
                console.log(`❌ Error loading owner index for '${firstChar}':`, err);
            }
        }
        
        // Check if this is an exact owner search (case-insensitive)
        let ownerKey = null;
        if (indexData) {
            // Find the actual owner key (case-insensitive match)
            ownerKey = Object.keys(indexData).find(key => key.toLowerCase() === query);
        }
        
        if (ownerKey && indexData[ownerKey]) {
            console.log(`🚀 Using owner index for '${ownerKey}'`);
            let ownerProjects = indexData[ownerKey];
            console.log(`📊 Total projects from index: ${ownerProjects.length}`);
            const matchCounts = {};
            
            // Count by language (include ALL languages including Other)
            const allLangs = [...languages, 'Other'];
            allLangs.forEach(lang => {
                matchCounts[lang] = ownerProjects.filter(p => p.language === lang).length;
            });
            
            console.log(`📈 Match counts:`, matchCounts);
            console.log(`🎯 showAll: ${showAll}, selectedLanguages:`, selectedLanguages);
            
            // Filter by selected languages if not showing all
            if (!showAll && selectedLanguages.length > 0) {
                ownerProjects = ownerProjects.filter(p => selectedLanguages.includes(p.language));
                console.log(`🔍 After language filter: ${ownerProjects.length} projects`);
            }
            
            setSearchMatchCounts(matchCounts);
            
            // Sort by score and paginate
            const allMatchingRepos = [...ownerProjects];
            allMatchingRepos.sort((a, b) => b.score - a.score);
            const pageSize = 50;
            const startIndex = (currentPage - 1) * pageSize;
            const pageRepos = allMatchingRepos.slice(startIndex, startIndex + pageSize);
            
            setRepos(pageRepos);
            
            if (pageRepos.length > 0) {
                const pageMax = Math.max(...pageRepos.map(r => r.score));
                if (pageMax > maxScore) setMaxScore(pageMax);
            }
            
            setIsLoading(false);
            return;
        }
        
        // Fall back to traditional search (for partial matches)
        // But only if query is at least 2 characters (avoid too broad searches)
        if (query.length < 2) {
            console.log(`⏭️ Query too short, skipping search: '${query}'`);
            setIsLoading(false);
            return;
        }
        
        console.log(`🔍 Searching pages for '${query}'`);
        const allMatchingRepos = [];
        const matchCounts = {};

        languages.forEach(lang => {
            matchCounts[lang] = 0;
        });

        const langsToSearch = (showAll || selectedLanguages.length === 0) ? [...languages, 'Other'] : selectedLanguages;
        
        // Load in batches for better performance, but always load enough to get accurate count
        const batchSize = 10; // Load 10 pages at a time per language
        const maxBatches = 10; // Max 100 pages total

        for (let currentBatch = 0; currentBatch < maxBatches; currentBatch++) {
            const batchPromises = langsToSearch.map(async (lang) => {
                const startPage = currentBatch * batchSize + 1;
                const endPage = Math.min(
                    (currentBatch + 1) * batchSize,
                    metadata.languages[lang].pages
                );
                
                if (startPage > metadata.languages[lang].pages) {
                    return { lang, matches: [] };
                }

                const langMatches = [];

                for (let page = startPage; page <= endPage; page++) {
                    try {
                        const langPath = lang.toLowerCase().replace(/\+/g, "plus");
                        const pageUrl = `${process.env.PUBLIC_URL}/pages/${langPath}/page_${page}.json`;
                        const response = await fetch(pageUrl);
                        const pageData = await response.json();

                        // Apply search filter with relevance scoring
                        const filtered = pageData.filter(repo => {
                            const searchFields = [
                                repo.name.toLowerCase(),
                                repo.owner.toLowerCase(),
                                (repo.description || '').toLowerCase(),
                                ...(repo.topics || []).map(t => t.toLowerCase())
                            ];
                            return searchFields.some(field => field.includes(query));
                        }).map(repo => {
                            // Calculate relevance score
                            let relevance = 0;
                            const nameLower = repo.name.toLowerCase();
                            const ownerLower = repo.owner.toLowerCase();
                            const descLower = (repo.description || '').toLowerCase();
                            const topics = (repo.topics || []).map(t => t.toLowerCase());
                            
                            // Exact match in name (highest priority)
                            if (nameLower === query) relevance += 1000;
                            else if (nameLower.includes(query)) relevance += 500;
                            
                            // Exact match in owner
                            if (ownerLower === query) relevance += 800;
                            else if (ownerLower.includes(query)) relevance += 400;
                            
                            // Match in topics
                            if (topics.some(t => t === query)) relevance += 300;
                            else if (topics.some(t => t.includes(query))) relevance += 150;
                            
                            // Match in description (lowest priority)
                            if (descLower.includes(query)) relevance += 50;
                            
                            return { ...repo, language: lang, relevance };
                        });

                        langMatches.push(...filtered);
                    } catch (err) {
                        console.error(`Failed to load ${lang} page ${page}:`, err);
                    }
                }

                return { lang, matches: langMatches };
            });

            // Wait for current batch to complete
            const batchResults = await Promise.all(batchPromises);
            
            // Add results and update counts
            batchResults.forEach(({ lang, matches }) => {
                allMatchingRepos.push(...matches);
                matchCounts[lang] = (matchCounts[lang] || 0) + matches.length;
            });
        }

        // Update match counts for display
        setSearchMatchCounts(matchCounts);

        // Sort by global rank (preserve original ranking)
        allMatchingRepos.sort((a, b) => {
            return (a.global_rank || 999999) - (b.global_rank || 999999);
        });
        
        const pageSize = 50;
        const startIndex = (currentPage - 1) * pageSize;
        const pageRepos = allMatchingRepos.slice(startIndex, startIndex + pageSize);

        setRepos(pageRepos);

        if (pageRepos.length > 0) {
            const pageMax = Math.max(...pageRepos.map((r) => r.score));
            if (pageMax > maxScore) setMaxScore(pageMax);
        }

        setIsLoading(false);
    };

    // Handle language checkbox toggle
    const handleLanguageToggle = (lang) => {
        setShowAll(false); // Uncheck "All" when selecting specific languages
        setSelectedLanguages((prev) => {
            if (prev.includes(lang)) {
                const newSelected = prev.filter((l) => l !== lang);
                // If no languages selected, go back to "All"
                if (newSelected.length === 0) {
                    setShowAll(true);
                }
                return newSelected;
            } else {
                return [...prev, lang];
            }
        });
        setCurrentPage(1); // Reset to page 1 when filter changes
    };

    // Handle "All" checkbox toggle
    const handleAllToggle = () => {
        if (!showAll) {
            setShowAll(true);
            setSelectedLanguages([]);
            setCurrentPage(1);
        }
    };

    // Calculate total pages
    const getTotalPages = () => {
        const MAX_PROJECTS = 10000;
        const MAX_PAGES = Math.ceil(MAX_PROJECTS / 50); // 200 pages
        
        if (showAll && !debouncedSearchQuery.trim()) {
            // Mixed mode: calculate total from all languages, limited to 10000
            let total = 0;
            languages.forEach((lang) => {
                if (metadata.languages[lang]) {
                    total += metadata.languages[lang].total;
                }
            });
            const calculatedPages = Math.ceil(total / 50);
            return Math.min(calculatedPages, MAX_PAGES);
        } else if (!debouncedSearchQuery.trim() && selectedLanguages.length > 0) {
            // Selected languages mode: calculate from selected languages, limited to 10000
            let total = 0;
            selectedLanguages.forEach((lang) => {
                if (metadata.languages[lang]) {
                    total += metadata.languages[lang].total;
                }
            });
            const calculatedPages = Math.ceil(total / 50);
            return Math.min(calculatedPages, MAX_PAGES);
        } else if (debouncedSearchQuery.trim()) {
            // Search mode: no limit, show all search results
            const totalMatches = Object.values(searchMatchCounts).reduce((sum, count) => sum + count, 0);
            if (totalMatches === 0) {
                // Still loading search results
                return currentPage;
            }
            return Math.ceil(totalMatches / 50);
        } else {
            return 1;
        }
    };

    const totalPages = getTotalPages();

    // Fetch repository details when mouse hovers
    const fetchRepoDetails = async (repo) => {
        if (repoDetails[repo.name]) {
            return; // Already fetched
        }

        // Use the data we already have from the JSON (including topics if available)
        setRepoDetails((prev) => ({
            ...prev,
            [repo.name]: {
                description: repo.description || "No description available",
                language: repo.language || "Unknown",
                topics: repo.topics || []
            }
        }));
    };

    // Get repository description
    const getRepoDescription = (repo) => {
        const details = repoDetails[repo.name];
        if (!details) {
            return `⭐ ${repo.stars.toLocaleString()} stars | 🍴 ${repo.forks.toLocaleString()} forks | 🐛 ${repo.issues.toLocaleString()} issues`;
        }

        const hasTechStack = details.topics && details.topics.length > 0;
        return (
            <div>
                <div style={{ marginBottom: "8px" }}>
                    <strong>Language:</strong> {details.language}
                </div>
                {hasTechStack && (
                    <div style={{ marginBottom: "8px" }}>
                        <strong>Tech Stack:</strong>{" "}
                        {details.topics.slice(0, 5).join(", ")}
                    </div>
                )}
                <div style={{ marginBottom: "8px" }}>
                    <strong>Description:</strong> {details.description}
                </div>
                <div>
                    ⭐ {repo.stars.toLocaleString()} stars | 🍴{" "}
                    {repo.forks.toLocaleString()} forks | 🐛{" "}
                    {repo.issues.toLocaleString()} issues
                </div>
            </div>
        );
    };

    return (
        <div className="container">
            <Link to="/" className="back-btn">
                ‹ Back
            </Link>

            <header>
                <h1>Seattle Source Ranker</h1>
                <p className="subtitle">
                    Top Open-Source Projects by Seattle-Area Developers
                </p>
                {metadata && metadata.last_updated && (
                    <p className="last-updated">Last updated: {metadata.last_updated}</p>
                )}
            </header>

            {/* Search Bar */}
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
                                setCurrentPage(1);
                                setPageCache({}); // Clear cache when clearing search
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
                {isLoading && (
                    <div className="search-hint">
                        <span className="spinner"></span> Searching...
                    </div>
                )}
            </div>

            {/* Language Filter Toggle Button */}
            <button 
                className="filter-toggle-btn"
                onClick={() => setShowFilters(!showFilters)}
            >
                <span>{showFilters ? '▼' : '▶'}</span> Filter by Language
                {!showAll && selectedLanguages.length > 0 && (
                    <span className="active-filter-badge">{selectedLanguages.length}</span>
                )}
            </button>

            {/* Language Filter Checkboxes */}
            {showFilters && (
                <div className="language-filters">
                    <div className="checkbox-grid">
                        {/* All option */}
                        <label className="checkbox-label checkbox-label-all">
                            <input
                                type="checkbox"
                                checked={showAll}
                                onChange={handleAllToggle}
                            />
                            <span className="checkbox-text">
              <strong>All</strong>
                                {metadata && (
                                    <span className="lang-count">
                                        {debouncedSearchQuery.trim() && Object.keys(searchMatchCounts).length > 0 ? (
                                            `(${Object.values(searchMatchCounts).reduce((sum, count) => sum + count, 0).toLocaleString()} matches)`
                                        ) : (
                                            `(${Object.keys(metadata.languages).reduce((sum, lang) => sum + (metadata.languages[lang]?.total || 0), 0).toLocaleString()})`
                                        )}
                </span>
                                )}
            </span>
                        </label>

                        {/* Individual languages */}
                        {languages.map((lang) => (
                            <label key={lang} className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={selectedLanguages.includes(lang)}
                                    onChange={() => handleLanguageToggle(lang)}
                                />
                                <span className="checkbox-text">
                {lang}
                                    {metadata && metadata.languages[lang] && (
                                        <span className="lang-count">
                                            {debouncedSearchQuery.trim() ? (
                                                // During search, show match count if available, otherwise show original count
                                                searchMatchCounts[lang] !== undefined ?
                                                    `(${searchMatchCounts[lang].toLocaleString()} ${searchMatchCounts[lang] === 1 ? 'match' : 'matches'})` :
                                                    `(${metadata.languages[lang].total.toLocaleString()})`
                                            ) : (
                                                `(${metadata.languages[lang].total.toLocaleString()})`
                                            )}
                  </span>
                                    )}
              </span>
                            </label>
                        ))}
                    </div>
                </div>
            )}

            {/* Ranking Table */}
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
                    {repos.map((repo, index) => {
                        // Use global rank if available, otherwise calculate
                        const displayRank = repo.global_rank || ((currentPage - 1) * 50 + index + 1);
                        const barWidth = (repo.score / maxScore) * 100;
                        // Handle score display: remove "0.", e.g., 0.88 -> 88, 1.23 -> 123
                        let displayScore;
                        if (repo.score < 1) {
                            displayScore = (repo.score * 100).toFixed(0);
                        } else {
                            displayScore = (repo.score * 100).toFixed(0);
                        }

                        // Extract project name (remove owner/ prefix)
                        const projectName = repo.name.includes("/")
                            ? repo.name.split("/")[1]
                            : repo.name;

                        return (
                            <tr key={repo.name}>
                                <td className="rank-col">#{displayRank}</td>
                                <td className="owner-col">
                                    <span
                                        className="owner-link"
                                        onClick={() => handleOwnerClick(repo.owner)}
                                        title={`Search for ${repo.owner}`}
                                    >
                                        {repo.owner}
                                    </span>
                                </td>
                                <td className="chart-col">
                                    <div
                                        className="bar-container"
                                        onMouseEnter={(e) => {
                                            // Clear any pending close operations
                                            if (timeoutRef.current) {
                                                clearTimeout(timeoutRef.current);
                                            }
                                            
                                            // Calculate tooltip position
                                            const container = e.currentTarget;
                                            const rect = container.getBoundingClientRect();
                                            const viewportHeight = window.innerHeight;
                                            const tooltipHeight = 200; // Approximate tooltip height
                                            const spaceBelow = viewportHeight - rect.bottom;
                                            
                                            // If not enough space below, show tooltip above
                                            const showAbove = spaceBelow < tooltipHeight + 20;
                                            
                                            setTooltipPosition({
                                                [repo.name]: showAbove
                                            });
                                            setHoveredRepo(repo.name);
                                            fetchRepoDetails(repo);
                                        }}
                                        onMouseLeave={() => {
                                            // Delay close to allow mouse to move to tooltip
                                            timeoutRef.current = setTimeout(() => {
                                                setHoveredRepo(null);
                                            }, 150);
                                        }}
                                    >
                                        <a
                                            href={repo.html_url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="bar-link"
                                        >
                                            <div
                                                className="bar"
                                                style={{ width: `${barWidth}%` }}
                                            >
                          <span className="project-name">
                            {projectName}
                          </span>
                                            </div>
                                        </a>
                                        {hoveredRepo === repo.name && (
                                            <div
                                                className={`tooltip ${tooltipPosition[repo.name] ? 'tooltip-above' : ''}`}
                                                onMouseEnter={() => {
                                                    // Clear close operation
                                                    if (timeoutRef.current) {
                                                        clearTimeout(timeoutRef.current);
                                                    }
                                                    setHoveredRepo(repo.name);
                                                }}
                                                onMouseLeave={() => {
                                                    setHoveredRepo(null);
                                                }}
                                            >
                                                <div className="tooltip-title">
                                                    {projectName}
                                                </div>
                                                <div className="tooltip-desc">
                                                    {getRepoDescription(repo)}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </td>
                                <td className="score-col">{displayScore}</td>
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
                {showAll && !debouncedSearchQuery.trim() ? (
                    <>
                        Showing {(currentPage - 1) * 50 + 1}-
                        {Math.min(
                            currentPage * 50,
                            10000 // Max displayable projects
                        )}{" "}
                        of{" "}
                        {Math.min(
                            metadata
                                ? Object.keys(metadata.languages).reduce(
                                    (sum, lang) => sum + metadata.languages[lang].total,
                                    0
                                )
                                : 0,
                            10000
                        ).toLocaleString()}{" "}
                        projects
                    </>
                ) : !debouncedSearchQuery.trim() &&
                selectedLanguages.length > 0 ? (
                    <>
                        Showing {(currentPage - 1) * 50 + 1}-
                        {Math.min(
                            currentPage * 50,
                            Math.min(
                                selectedLanguages.reduce(
                                    (sum, lang) =>
                                        sum + (metadata.languages[lang]?.total || 0),
                                    0
                                ),
                                10000
                            )
                        )}{" "}
                        of{" "}
                        {Math.min(
                            selectedLanguages.reduce(
                                (sum, lang) => sum + (metadata.languages[lang]?.total || 0),
                                0
                            ),
                            10000
                        ).toLocaleString()}{" "}
                        projects
                    </>
                ) : debouncedSearchQuery.trim() && Object.keys(searchMatchCounts).length > 0 ? (
                    <>
                        Showing {repos.length > 0 ? (currentPage - 1) * 50 + 1 : 0}-
                        {repos.length > 0
                            ? (currentPage - 1) * 50 + repos.length
                            : 0}{" "}
                        of {Object.values(searchMatchCounts).reduce((sum, count) => sum + count, 0).toLocaleString()} matches
                    </>
                ) : (
                    <>
                        Showing {repos.length > 0 ? (currentPage - 1) * 50 + 1 : 0}-
                        {repos.length > 0
                            ? (currentPage - 1) * 50 + repos.length
                            : 0}{" "}
                        {isLoading && <span className="spinner" style={{display: 'inline-block', marginLeft: '8px'}}></span>}
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
                        disabled={currentPage === 1 || isLoading}
                        title="First page"
                    >
                        «
                    </button>
                    
                    <button
                        className="pagination-btn"
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1 || isLoading}
                        title="Previous page"
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
                                        setCurrentPage(pageNum);
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
                            disabled={isLoading}
                        />
                        <span className="page-total">/ {totalPages.toLocaleString()}</span>
                    </div>
                    
                    <button
                        className="pagination-btn"
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages || isLoading}
                        title="Next page"
                    >
                        ›
                    </button>
                    
                    <button
                        className="pagination-btn pagination-edge"
                        onClick={() => setCurrentPage(totalPages)}
                        disabled={currentPage === totalPages || isLoading}
                        title="Last page"
                    >
                        »
                    </button>
                </div>
            )}
        </div>
    );
}
