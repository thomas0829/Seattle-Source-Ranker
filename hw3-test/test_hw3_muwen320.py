#!/usr/bin/env python3
"""
Homework 3 - Testing Assignment
Author: Muwen320
Tests for Seattle Source Ranker project
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 和 thomas 一样：把项目根目录加进 sys.path 里，方便导入本地模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.token_manager import TokenManager
from scripts.generate_frontend_data import (
    normalize,
    age_factor,
    calculate_github_score,
)


def test_github_score_smoke_basic():
    """
    author: Muwen320
    reviewer: Wenshu0206
    category: smoke test

    Smoke test:
    最基础的端到端测试——给一个合理的 project 字典，
    确认 calculate_github_score 能跑完，并返回非负数值。
    （不关心具体分数，只关心“能正常跑起来”）
    """
    now = datetime.now(timezone.utc)
    created = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pushed = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    project = {
        "stars": 50,
        "forks": 20,
        "watchers": 10,
        "open_issues": 5,
        "created_at": created,
        "pushed_at": pushed,
    }

    score = calculate_github_score(project, max_stars=1000, max_forks=500, max_watchers=200)

    assert isinstance(score, (int, float))
    assert score >= 0


def test_normalize_one_shot_full_value():
    """
    author: Muwen320
    reviewer: Wenshu0206
    category: one-shot test

    One-shot:
    固定输入输出对：当 value == max_value 时，归一化结果应该精确等于 1.0。
    """
    result = normalize(100, 100)
    assert result == 1.0, f"Expected 1.0 but got {result}"


def test_github_score_edge_many_issues():
    """
    author: Muwen320
    reviewer: Chase-Zou
    category: edge test

    Edge test:
    在其他条件完全相同的情况下，打开 issue 的数量从很少增加到非常多，
    总分应该不会“变高”（也就是 many_issues 的分数 <= few_issues）。
    """
    now = datetime.now(timezone.utc)
    created = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pushed = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    base = {
        "stars": 500,
        "forks": 100,
        "watchers": 80,
        "created_at": created,
        "pushed_at": pushed,
    }

    project_few_issues = {**base, "open_issues": 1}
    project_many_issues = {**base, "open_issues": 5000}

    score_few = calculate_github_score(project_few_issues, 10_000, 5_000, 2_000)
    score_many = calculate_github_score(project_many_issues, 10_000, 5_000, 2_000)

    assert score_many <= score_few, (
        f"Expected score with many issues <= score with few issues, "
        f"got many={score_many}, few={score_few}"
    )


def test_age_factor_pattern_time_ordering():
    """
    author: Muwen320
    reviewer: Chase-Zou
    category: pattern test

    Pattern test:
    同一个函数 age_factor，关注的模式和 thomas 不一样——
    我们测试：项目“越老”，age_factor 越大（或至少不更小）。
    """
    now = datetime.now(timezone.utc)

    # 非常新的项目（3 天）
    created_new = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # 中等年龄项目（1 年）
    created_mid = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # 很老的项目（5 年）
    created_old = (now - timedelta(days=5 * 365)).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_score = age_factor(created_new)
    mid_score = age_factor(created_mid)
    old_score = age_factor(created_old)

    # 所有分数都应该在 [0,1] 范围内
    for s in (new_score, mid_score, old_score):
        assert 0.0 <= s <= 1.0

    # 模式：项目越老，age_factor 不应低于“更新”的项目
    assert new_score <= mid_score <= old_score, (
        f"Expected new <= mid <= old, got "
        f"new={new_score}, mid={mid_score}, old={old_score}"
    )