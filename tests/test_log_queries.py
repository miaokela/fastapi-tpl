#!/usr/bin/env python
"""
日志查询功能演示和测试脚本
"""

import subprocess
import json
from pathlib import Path


def test_log_queries():
    """测试各种日志查询"""
    log_file = Path("logs/2025-12-23.log")
    
    if not log_file.exists():
        print("❌ 日志文件不存在")
        return
    
    # 测试用例
    test_cases = [
        {
            "name": "查询所有日志",
            "filter": "."
        },
        {
            "name": "查询user_id为123的记录",
            "filter": "select(.user_id == 123)"
        },
        {
            "name": "查询包含'成功'的消息",
            "filter": "select(.message | contains(\"成功\"))"
        },
        {
            "name": "按duration_ms倒序排列（最慢的5个）",
            "filter": "select(.duration_ms) | sort_by(.duration_ms) | reverse | .[0:5]"
        },
        {
            "name": "按operation分组统计",
            "filter": "group_by(.operation) | map({operation: .[0].operation, count: length})"
        },
        {
            "name": "查询超过50ms的操作",
            "filter": "select(has(\"duration_ms\") and .duration_ms > 50)"
        },
    ]
    
    print("\n" + "="*60)
    print("日志查询功能测试")
    print("="*60 + "\n")
    
    for test in test_cases:
        print(f"🔍 {test['name']}")
        print(f"   jq filter: {test['filter']}\n")
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                result = subprocess.run(
                    ["jq", test["filter"]],
                    stdin=f,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            if result.returncode == 0:
                # 计算结果数量
                output_lines = [l for l in result.stdout.strip().split("\n") if l]
                count = len(output_lines)
                
                print(f"   ✅ 成功 - 找到 {count} 条记录")
                
                # 显示前2条结果
                for i, line in enumerate(output_lines[:2]):
                    try:
                        data = json.loads(line)
                        print(f"      [{i+1}] {json.dumps(data, ensure_ascii=False, indent=10)[:100]}...")
                    except:
                        print(f"      [{i+1}] {line[:100]}...")
                
                if count > 2:
                    print(f"      ... 还有 {count - 2} 条记录")
            else:
                print(f"   ❌ 失败: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            print(f"   ❌ 超时")
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
        
        print()


if __name__ == "__main__":
    test_log_queries()
    
    print("\n" + "="*60)
    print("日志文件信息")
    print("="*60 + "\n")
    
    log_dir = Path("logs")
    if log_dir.exists():
        files = sorted(log_dir.glob("*.log"), reverse=True)
        for f in files:
            size = f.stat().st_size
            lines = sum(1 for _ in open(f))
            print(f"📄 {f.name:20} | 大小: {size:>10,} bytes | 行数: {lines:>6}")
