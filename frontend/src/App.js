import React, { useEffect, useState, useRef } from "react";
import "./App.css";

export default function App() {
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
  const timeoutRef = useRef(null);
  const searchTimeoutRef = useRef(null);
  const [pageInput, setPageInput] = useState("");
  const [searchMatchCounts, setSearchMatchCounts] = useState({});

  // Load metadata
  useEffect(() => {
    fetch(`${process.env.PUBLIC_URL}/metadata.json`)
      .then((res) => res.json())
      .then((data) => {
        setMetadata(data);
        const langs = Object.keys(data.languages)
          .filter(lang => lang !== "Other")
          .sort((a, b) => data.languages[b].total - data.languages[a].total);
        setLanguages(langs);
      })
      .catch((err) => console.error("❌ Failed to load metadata:", err));
  }, []);

  // Debounce search query
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
      setCurrentPage(1); // Reset to page 1 when search changes
      if (!searchQuery.trim()) {
        setSearchMatchCounts({}); // Clear match counts when search is cleared
      }
    }, 500); // Wait 500ms after user stops typing

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

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

  // Load mixed page (all languages, lazy loading)
  const loadMixedPage = async () => {
    const cacheKey = `mixed_${currentPage}`;
    if (pageCache[cacheKey]) {
      setRepos(pageCache[cacheKey]);
      return;
    }

    setIsLoading(true);
    const pageSize = 50;
    
    // Calculate which language pages to load based on current page
    // We need to load enough pages to get to the current page
    const reposPerLoad = pageSize * currentPage;
    const allReposForLoad = [];
    
    // Load pages from each language until we have enough repos
    const maxPagesToLoadPerLang = Math.ceil(reposPerLoad / languages.length / pageSize) + 1;
    
    for (const lang of languages) {
      const totalPagesForLang = metadata.languages[lang].pages;
      const pagesToLoad = Math.min(maxPagesToLoadPerLang, totalPagesForLang);
      
      for (let page = 1; page <= pagesToLoad; page++) {
        const langPath = lang.toLowerCase().replace(/\+/g, 'plus');
        const pageUrl = `${process.env.PUBLIC_URL}/pages/${langPath}/page_${page}.json`;
        
        try {
          const response = await fetch(pageUrl);
          const pageData = await response.json();
          const reposWithLang = pageData.map(repo => ({ ...repo, language: lang }));
          allReposForLoad.push(...reposWithLang);
        } catch (err) {
          console.error(`Failed to load ${lang} page ${page}:`, err);
        }
      }
    }
    
    // Sort by score and get the specific page
    allReposForLoad.sort((a, b) => b.score - a.score);
    const startIndex = (currentPage - 1) * pageSize;
    const pageRepos = allReposForLoad.slice(startIndex, startIndex + pageSize);
    
    setRepos(pageRepos);
    setPageCache(prev => ({ ...prev, [cacheKey]: pageRepos }));
    
    if (pageRepos.length > 0) {
      const pageMax = Math.max(...pageRepos.map(r => r.score));
      if (pageMax > maxScore) setMaxScore(pageMax);
    }
    
    setIsLoading(false);
  };

  // Load selected languages (need to load enough pages to get to current page)
  const loadSelectedLanguages = async () => {
    const cacheKey = `langs_${selectedLanguages.join(',')}_${currentPage}`;
    if (pageCache[cacheKey]) {
      setRepos(pageCache[cacheKey]);
      return;
    }

    setIsLoading(true);
    const pageSize = 50;
    const allReposForLoad = [];
    
    // Calculate how many pages we need to load from each language
    const reposNeeded = pageSize * currentPage;
    const maxPagesToLoadPerLang = Math.ceil(reposNeeded / selectedLanguages.length / pageSize) + 1;
    
    for (const lang of selectedLanguages) {
      const totalPagesForLang = metadata.languages[lang].pages;
      const pagesToLoad = Math.min(maxPagesToLoadPerLang, totalPagesForLang);
      
      for (let page = 1; page <= pagesToLoad; page++) {
        const langPath = lang.toLowerCase().replace(/\+/g, 'plus');
        const pageUrl = `${process.env.PUBLIC_URL}/pages/${langPath}/page_${page}.json`;
        
        try {
          const response = await fetch(pageUrl);
          const pageData = await response.json();
          const reposWithLang = pageData.map(repo => ({ ...repo, language: lang }));
          allReposForLoad.push(...reposWithLang);
        } catch (err) {
          console.error(`Failed to load ${lang} page ${page}:`, err);
        }
      }
    }
    
    // Sort by score and get the specific page
    allReposForLoad.sort((a, b) => b.score - a.score);
    const startIndex = (currentPage - 1) * pageSize;
    const pageRepos = allReposForLoad.slice(startIndex, startIndex + pageSize);
    
    setRepos(pageRepos);
    setPageCache(prev => ({ ...prev, [cacheKey]: pageRepos }));
    
    if (pageRepos.length > 0) {
      const pageMax = Math.max(...pageRepos.map(r => r.score));
      if (pageMax > maxScore) setMaxScore(pageMax);
    }
    
    setIsLoading(false);
  };

  // Load search results (need to load all pages for accurate search)
  const loadSearchResults = async () => {
    setIsLoading(true);
    const allMatchingRepos = [];
    const matchCounts = {}; // Track matches per language
    
    // Initialize all languages to 0 matches
    languages.forEach(lang => {
      matchCounts[lang] = 0;
    });
    
    // Determine which languages to search
    // If showAll is true OR selectedLanguages is empty, search all languages
    const langsToSearch = (showAll || selectedLanguages.length === 0) ? languages : selectedLanguages;
    
    // Reduced limit for better performance - only search first 10 pages per language
    const maxPagesToLoad = 10; // Reduced from 20 for better performance
    
    const query = debouncedSearchQuery.toLowerCase();
    
    // Load pages in parallel for better performance
    const loadPromises = langsToSearch.map(async (lang) => {
      const totalPages = Math.min(metadata.languages[lang].pages, maxPagesToLoad);
      const langMatches = [];
      
      for (let page = 1; page <= totalPages; page++) {
        try {
          const langPath = lang.toLowerCase().replace(/\+/g, 'plus');
          const pageUrl = `${process.env.PUBLIC_URL}/pages/${langPath}/page_${page}.json`;
          const response = await fetch(pageUrl);
          const pageData = await response.json();
          
          // Apply search filter immediately
          const filtered = pageData.filter(repo => 
            repo.name.toLowerCase().includes(query) ||
            repo.owner.toLowerCase().includes(query)
          ).map(repo => ({ ...repo, language: lang }));
          
          langMatches.push(...filtered);
        } catch (err) {
          console.error(`Failed to load ${lang} page ${page}:`, err);
        }
      }
      
      matchCounts[lang] = langMatches.length;
      return langMatches;
    });
    
    // Wait for all languages to finish loading
    const results = await Promise.all(loadPromises);
    results.forEach(langRepos => allMatchingRepos.push(...langRepos));
    
    // Update match counts for display
    setSearchMatchCounts(matchCounts);
    
    // Sort by score and paginate
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
  };

  // Handle language checkbox toggle
  const handleLanguageToggle = (lang) => {
    setShowAll(false); // Uncheck "All" when selecting specific languages
    setSelectedLanguages(prev => {
      if (prev.includes(lang)) {
        const newSelected = prev.filter(l => l !== lang);
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

  // Handle page jump
  const handlePageJump = (e) => {
    e.preventDefault();
    const pageNum = parseInt(pageInput);
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages) {
      setCurrentPage(pageNum);
      setPageInput("");
    }
  };

  // Calculate total pages
  const getTotalPages = () => {
    if (showAll && !debouncedSearchQuery.trim()) {
      // Mixed mode: calculate total from all languages
      let total = 0;
      languages.forEach(lang => {
        if (metadata.languages[lang]) {
          total += metadata.languages[lang].total;
        }
      });
      return Math.ceil(total / 50);
    } else if (!debouncedSearchQuery.trim() && selectedLanguages.length > 0) {
      // Selected languages mode: calculate from selected languages
      let total = 0;
      selectedLanguages.forEach(lang => {
        if (metadata.languages[lang]) {
          total += metadata.languages[lang].total;
        }
      });
      return Math.ceil(total / 50);
    } else {
      // Search mode: we don't know exact total, show estimated
      return repos.length === 50 ? currentPage + 1 : currentPage;
    }
  };

  const totalPages = getTotalPages();

  // Fetch repository details when mouse hovers
  const fetchRepoDetails = async (repo) => {
    if (repoDetails[repo.name]) {
      return; // Already fetched
    }
    
    // Use the data we already have from the JSON (including topics if available)
    setRepoDetails(prev => ({
      ...prev,
      [repo.name]: {
        description: repo.description || 'No description available',
        language: repo.language || 'Unknown',
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
        <div style={{ marginBottom: '8px' }}>
          <strong>Language:</strong> {details.language}
        </div>
        {hasTechStack && (
          <div style={{ marginBottom: '8px' }}>
            <strong>Tech Stack:</strong> {details.topics.slice(0, 5).join(', ')}
          </div>
        )}
        <div style={{ marginBottom: '8px' }}>
          <strong>Description:</strong> {details.description}
        </div>
        <div>
          ⭐ {repo.stars.toLocaleString()} stars | 🍴 {repo.forks.toLocaleString()} forks | 🐛 {repo.issues.toLocaleString()} issues
        </div>
      </div>
    );
  };

  return (
    <div className="container">
      <header>
        <h1>Seattle-Source-Ranker</h1>
        <p className="subtitle">Top Open-Source Projects by Seattle-Area Developers</p>
        {metadata && metadata.last_updated && (
          <p className="last-updated">Last updated: {metadata.last_updated}</p>
        )}
      </header>

      {/* Search Bar */}
      <div className="search-container">
        <input
          type="text"
          className="search-input"
          placeholder="🔍 Search by project name or owner..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        {searchQuery !== debouncedSearchQuery && (
          <div className="search-hint">Searching...</div>
        )}
        {debouncedSearchQuery && (
          <div className="search-hint">
            Searching in top 10 pages per language (top ~{showAll ? languages.length * 500 : selectedLanguages.length * 500} projects)
          </div>
        )}
      </div>

      {/* Language Filter Checkboxes */}
      <div className="language-filters">
        <div className="filter-title">Filter by Language:</div>
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
          {languages.map(lang => (
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

      {/* Page Info */}
      <div style={{ textAlign: 'center', margin: '15px 0', color: '#666', fontSize: '0.9em' }}>
        {showAll && !debouncedSearchQuery.trim() ? (
          <>
            Showing {((currentPage - 1) * 50) + 1}-{Math.min(currentPage * 50, metadata ? Object.keys(metadata.languages).reduce((sum, lang) => sum + metadata.languages[lang].total, 0) : 0)} of {metadata ? Object.keys(metadata.languages).reduce((sum, lang) => sum + metadata.languages[lang].total, 0).toLocaleString() : '0'} projects
          </>
        ) : !debouncedSearchQuery.trim() && selectedLanguages.length > 0 ? (
          <>
            Showing {((currentPage - 1) * 50) + 1}-{Math.min(currentPage * 50, selectedLanguages.reduce((sum, lang) => sum + (metadata.languages[lang]?.total || 0), 0))} of {selectedLanguages.reduce((sum, lang) => sum + (metadata.languages[lang]?.total || 0), 0).toLocaleString()} projects
          </>
        ) : debouncedSearchQuery.trim() && Object.keys(searchMatchCounts).length > 0 ? (
          <>
            Showing {repos.length > 0 ? ((currentPage - 1) * 50) + 1 : 0}-{repos.length > 0 ? ((currentPage - 1) * 50) + repos.length : 0} of {Object.values(searchMatchCounts).reduce((sum, count) => sum + count, 0).toLocaleString()} matches
          </>
        ) : (
          <>
            Showing {repos.length > 0 ? ((currentPage - 1) * 50) + 1 : 0}-{repos.length > 0 ? ((currentPage - 1) * 50) + repos.length : 0} (searching...)
          </>
        )}
        {isLoading && <span> ⏳</span>}
      </div>

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
              const globalRank = (currentPage - 1) * 50 + index + 1;
              const barWidth = (repo.score / maxScore) * 100;
              // Handle score display: remove "0.", e.g., 0.88 -> 88, 1.23 -> 123
              let displayScore;
              if (repo.score < 1) {
                displayScore = (repo.score * 100).toFixed(0);
              } else {
                displayScore = (repo.score * 100).toFixed(0);
              }
              
              // Extract project name (remove owner/ prefix)
              const projectName = repo.name.includes('/') ? repo.name.split('/')[1] : repo.name;
              
              return (
                <tr key={repo.name}>
                  <td className="rank-col">#{globalRank}</td>
                  <td className="owner-col">
                    <span 
                      className="owner-link" 
                      onClick={() => {
                        setSearchQuery(repo.owner);
                        setCurrentPage(1);
                      }}
                      title={`Search for ${repo.owner}`}
                    >
                      {repo.owner}
                    </span>
                  </td>
                  <td className="chart-col">
                    <div 
                      className="bar-container"
                      onMouseEnter={() => {
                        // Clear any pending close operations
                        if (timeoutRef.current) {
                          clearTimeout(timeoutRef.current);
                        }
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
                          <span className="project-name">{projectName}</span>
                        </div>
                      </a>
                      {hoveredRepo === repo.name && (
                        <div 
                          className="tooltip"
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
                          <div className="tooltip-title">{projectName}</div>
                          <div className="tooltip-desc">{getRepoDescription(repo)}</div>
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

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination-container">
          <button 
            className="pagination-btn"
            onClick={() => setCurrentPage(1)} 
            disabled={currentPage === 1 || isLoading}
          >
            <span className="pagination-icon">⏮</span>
            <span className="pagination-text">First</span>
          </button>
          <button 
            className="pagination-btn"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))} 
            disabled={currentPage === 1 || isLoading}
          >
            <span className="pagination-icon">◀</span>
            <span className="pagination-text">Previous</span>
          </button>
          <div className="pagination-info">
            <span className="current-page">{currentPage.toLocaleString()}</span>
            <span className="pagination-separator">/</span>
            <span className="total-pages">{totalPages.toLocaleString()}</span>
          </div>
          <button 
            className="pagination-btn"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} 
            disabled={currentPage === totalPages || isLoading}
          >
            <span className="pagination-text">Next</span>
            <span className="pagination-icon">▶</span>
          </button>
          <button 
            className="pagination-btn"
            onClick={() => setCurrentPage(totalPages)} 
            disabled={currentPage === totalPages || isLoading}
          >
            <span className="pagination-text">Last</span>
            <span className="pagination-icon">⏭</span>
          </button>
          
          {/* Page Jump Input */}
          <form onSubmit={handlePageJump} className="page-jump">
            <span className="page-jump-label">Go to:</span>
            <input
              type="number"
              className="page-jump-input"
              placeholder="Page"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              min="1"
              max={totalPages}
            />
            <button type="submit" className="page-jump-btn" disabled={isLoading}>
              →
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
