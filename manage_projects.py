#!/usr/bin/env python3
"""
Seattle Project Management Tool
For managing and updating Seattle project database
"""
import argparse
from collectors.incremental_collector import IncrementalProjectCollector


def main():
    parser = argparse.ArgumentParser(
        description="Seattle Project Database Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  # View current status
  python3 manage_projects.py --status
  
  # Refresh 7  day old data
  python3 manage_projects.py --refresh --days 7
  
  # 完整Updating(Refresh + 補充新專案)
  python3 manage_projects.py --full-update --target 10000
  
  # 只Collecting new projects(不Refresh)
  python3 manage_projects.py --collect-new --target 10000
        """
    )
    
    parser.add_argument(
        '--data-file',
        default='data/seattle_projects_10000.json',
        help='Data file path (default: data/seattle_projects_10000.json)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='View current database status'
    )
    
    parser.add_argument(
        '--refresh',
        action='store_true',
        help='Refresh stale project data'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Refreshing projects older than多少天的專案 (default: 7)'
    )
    
    parser.add_argument(
        '--collect-new',
        action='store_true',
        help='Collecting new projects(補充到目標數量)'
    )
    
    parser.add_argument(
        '--full-update',
        action='store_true',
        help='完整Updating(Refresh + Collecting new projects)'
    )
    
    parser.add_argument(
        '--target',
        type=int,
        default=10000,
        help='Target project count (default: 10000)'
    )
    
    args = parser.parse_args()
    
    # 初始化收集器
    print(f"🔧 Initializing project manager...")
    collector = IncrementalProjectCollector(data_file=args.data_file)
    
    # 執行操作
    if args.status:
        print_status(collector)
    
    elif args.refresh:
        print(f"\n🔄 Refreshing projects older than {args.days} 天的專案數據...")
        collector.refresh_stale_projects(days_old=args.days)
        print_status(collector)
    
    elif args.collect_new:
        print(f"\n📥 Collecting new projects(目標: {args.target})...")
        collector.collect_with_smart_update(
            target_count=args.target,
            refresh_days=0,  # 不Refresh
            collect_new=True
        )
        print_status(collector)
    
    elif args.full_update:
        print(f"\n🚀 執行完整Updating...")
        collector.collect_with_smart_update(
            target_count=args.target,
            refresh_days=args.days,
            collect_new=True
        )
        print_status(collector)
    
    else:
        # default顯示狀態
        print_status(collector)
        print("\n💡 使用 --help 查看所有選項")


def print_status(collector: IncrementalProjectCollector):
    """Print database status"""
    projects = collector.existing_projects
    
    print(f"\n" + "="*60)
    print(f"📊 Database Status")
    print(f"="*60)
    
    print(f"\n📦 Basic Info:")
    print(f"   Total Projects: {len(projects)}")
    print(f"   Data File: {collector.data_file}")
    
    if projects:
        # 星級統計
        total_stars = sum(p.get("stars", 0) for p in projects)
        avg_stars = total_stars / len(projects)
        
        print(f"\n⭐ Stars Statistics:")
        print(f"   Total Stars: {total_stars:,}")
        print(f"   Average Stars: {avg_stars:.1f}")
        print(f"   Highest: {projects[0]['stars']:,} ({projects[0]['name_with_owner']})")
        print(f"   Lowest: {projects[-1]['stars']:,} ({projects[-1]['name_with_owner']})")
        
        # Language Distribution
        languages = {}
        for p in projects:
            lang = p.get("language") or "Unknown"
            languages[lang] = languages.get(lang, 0) + 1
        
        print(f"\n🔤 Language Distribution (top 5):")
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        for lang, count in sorted_langs[:5]:
            print(f"   {lang:15s}: {count:5d} ({count/len(projects)*100:.1f}%)")
        
        # 星級Distribution
        star_ranges = {
            '10k+': sum(1 for p in projects if p.get("stars", 0) >= 10000),
            '5k-10k': sum(1 for p in projects if 5000 <= p.get("stars", 0) < 10000),
            '1k-5k': sum(1 for p in projects if 1000 <= p.get("stars", 0) < 5000),
            '100-1k': sum(1 for p in projects if 100 <= p.get("stars", 0) < 1000),
            '<100': sum(1 for p in projects if p.get("stars", 0) < 100),
        }
        
        print(f"\n📈 Stars Distribution:")
        for range_name, count in star_ranges.items():
            if count > 0:
                print(f"   {range_name:10s}: {count:5d} ({count/len(projects)*100:.1f}%)")
        
        # 前 10 專案
        print(f"\n🏆 Top 10 Projects:")
        for i, p in enumerate(projects[:10], 1):
            print(f"   {i:2d}. {p['name_with_owner']:45s} {p['stars']:6,} ⭐")
    
    print(f"\n" + "="*60)


if __name__ == "__main__":
    main()
