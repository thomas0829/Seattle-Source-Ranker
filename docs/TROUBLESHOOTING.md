# Troubleshooting Guide

## Common Issues

### Redis Connection Error
```bash
# Check if Redis system service is running
systemctl status redis-server
sudo systemctl start redis-server  # Start if stopped

# Test Redis connection
redis-cli ping  # Should return PONG
```

### Rate Limit Issues
- **Check token validity**: Ensure all tokens in `.env.tokens` are valid
- **Verify token rotation**: Logs show which token is active
- **Add more tokens**: Supports up to 6 tokens (currently using 6)
- **Check rate limits**: Each token has 5,000 GraphQL + 5,000 REST requests/hour

### Collection Failures
- **Review logs**: Check `logs/YYYYMMDD/` for error messages
- **GitHub Actions**: Verify all 6 tokens are added as Secrets
- **Cleanup issues**: Ensure `.collection_success` marker exists before cleanup
- **Worker timeout**: Increase timeout in `celery_config.py` if needed

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules package-lock.json  # Clean install
npm install
npm run build
```

### Watchers Update Slow
```bash
# Use 8 workers for faster processing (8x speedup)
python scripts/update_watchers.py --workers 8

# Single-threaded (slow): ~5 hours
# 8 workers (recommended): ~30-40 minutes
```

---

## Frequently Asked Questions

**Q: Why are watchers much lower than stars?**  
A: `watchers` = GitHub subscribers (notifications), `stars` = bookmarks. Typically 0.5%-4% ratio is normal. Projects with 10,000 stars often have only 50-400 watchers.

**Q: Why were some repositories removed?**  
A: ~2% of repos become inaccessible between collection and validation:
- **HTTP 451** - Legally blocked (DMCA, court order)
- **Deleted** - Owner deleted the repository
- **Private** - Changed from public to private

**Q: Can I use fewer than 6 tokens?**  
A: Yes, but collection will be slower. Minimum 1 token required. Each token adds 10,000 req/hr capacity (5k GraphQL + 5k REST).

**Q: Why is `data/seattle_projects_*.json` so large?**  
A: Contains full metadata for 450k+ repositories (~260MB). Not committed to Git. Only generated/processed locally and during GitHub Actions deployment.

**Q: How do I add more GitHub tokens?**  
A:
1. Generate tokens at https://github.com/settings/tokens
2. Required scopes: `public_repo` (read public repositories)
3. Add to `.env.tokens` as `GITHUB_TOKEN_7`, `GITHUB_TOKEN_8`, etc.
4. Update `TokenManager` to support more tokens if needed

**Q: What happens if I switch Git branches?**  
A: Local-only files (`.env.tokens`, `data/seattle_projects_*.json`, `frontend/public/pages/`) **persist across branch switches** - they are never committed to Git, so they stay on your machine.

**Q: Should I commit the generated frontend files?**  
A: **No**. Frontend data files are regenerated during deployment. Only commit:
- `data/seattle_users_*.json` (small user metadata)
- `data/seattle_pypi_projects.json` (PyPI list)
- `data/pypi_official_packages.json` (official packages)
- `README.md` (documentation)

---

## Back to Main Documentation

← [Return to README](../README.md) - Main project documentation and quick start guide
