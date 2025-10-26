import React, { useEffect, useState, useRef } from "react";
import "./App.css";

export default function App() {
  const [repos, setRepos] = useState([]);
  const [hoveredRepo, setHoveredRepo] = useState(null);
  const [maxScore, setMaxScore] = useState(1);
  const [repoDetails, setRepoDetails] = useState({});
  const timeoutRef = useRef(null);

  useEffect(() => {
    fetch("/ranked_project_local_seattle.json")
      .then((res) => res.json())
      .then((data) => {
        setRepos(data);
        // Find the highest score as baseline
        const max = Math.max(...data.map(r => r.score));
        setMaxScore(max);
      })
      .catch((err) => console.error("❌ Failed to load data:", err));
  }, []);

  // Fetch repository details when mouse hovers
  const fetchRepoDetails = async (repo) => {
    // Extract project name from full name
    const projectName = repo.name.includes('/') ? repo.name.split('/')[1] : repo.name;
    
    if (repoDetails[repo.name]) {
      return; // Already fetched
    }
    
    try {
      const response = await fetch(`https://api.github.com/repos/${repo.owner}/${projectName}`);
      const data = await response.json();
      setRepoDetails(prev => ({
        ...prev,
        [repo.name]: {
          description: data.description || 'No description available',
          language: data.language || 'Unknown',
          topics: data.topics || []
        }
      }));
    } catch (error) {
      console.error('Failed to fetch repo details:', error);
    }
  };

  // Get repository description
  const getRepoDescription = (repo) => {
    const details = repoDetails[repo.name];
    if (!details) {
      return `⭐ ${repo.stars.toLocaleString()} stars | 🍴 ${repo.forks.toLocaleString()} forks | 🐛 ${repo.issues.toLocaleString()} issues`;
    }
    
    const topics = details.topics.length > 0 ? details.topics.slice(0, 5).join(', ') : 'No topics';
    return (
      <div>
        <div style={{ marginBottom: '8px' }}>
          <strong>Language:</strong> {details.language}
        </div>
        <div style={{ marginBottom: '8px' }}>
          <strong>Topics:</strong> {topics}
        </div>
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
      </header>

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
                  <td className="rank-col">#{index + 1}</td>
                  <td className="owner-col">{repo.owner}</td>
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
    </div>
  );
}
