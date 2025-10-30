# seattle_source_ranker/ranker.py
class Ranker:
    def __init__(self, weights=None):
        self.weights = weights or {"stars": 0.4, "forks": 0.3, "watchers": 0.3}

    def compute_repo_score(self, repo):
        s = repo["stars"]
        f = repo["forks"]
        w = repo["watchers"]
        return (self.weights["stars"] * s +
                self.weights["forks"] * f +
                self.weights["watchers"] * w)

    def compute_user_score(self, user_repos):
        if not user_repos:
            return 0
        scores = [self.compute_repo_score(r) for r in user_repos]
        return sum(scores) / len(scores)

    def rank_users(self, users_with_repos):
        ranked = []
        for username, repos in users_with_repos.items():
            score = self.compute_user_score(repos)
            ranked.append({"username": username, "score": score})
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
