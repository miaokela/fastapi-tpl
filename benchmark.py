#!/usr/bin/env python3
"""
FastAPI 吞吐性能测试脚本

使用方法:
    python benchmark.py [--url URL] [--requests N] [--concurrency C]

示例:
    python benchmark.py                           # 默认测试
    python benchmark.py --requests 5000 --concurrency 100
    python benchmark.py --url http://192.168.1.100:8000
"""

import argparse
import asyncio
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass, field

try:
    import aiohttp
except ImportError:
    print("请先安装 aiohttp: pip install aiohttp")
    exit(1)


@dataclass
class BenchmarkResult:
    """测试结果"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    requests_per_second: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p50_latency: float
    p90_latency: float
    p99_latency: float
    latencies: List[float] = field(default_factory=list, repr=False)


class Benchmark:
    def __init__(self, base_url: str, total_requests: int, concurrency: int):
        self.base_url = base_url.rstrip('/')
        self.total_requests = total_requests
        self.concurrency = concurrency
        self.token: str = None
    
    async def login(self, session: aiohttp.ClientSession) -> bool:
        """登录获取 token"""
        try:
            async with session.post(
                f"{self.base_url}/auth/login",
                data={"username": "admin@example.com", "password": "admin123"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.token = data.get("access_token")
                    return True
                return False
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    async def make_request(
        self, 
        session: aiohttp.ClientSession, 
        method: str,
        endpoint: str,
        headers: dict = None,
        **kwargs
    ) -> tuple[bool, float]:
        """发起单个请求，返回 (是否成功, 延迟时间)"""
        url = f"{self.base_url}{endpoint}"
        start = time.perf_counter()
        try:
            async with session.request(method, url, headers=headers, **kwargs) as resp:
                await resp.read()
                latency = time.perf_counter() - start
                return resp.status < 400, latency
        except Exception:
            latency = time.perf_counter() - start
            return False, latency
    
    async def run_benchmark(
        self, 
        name: str,
        method: str,
        endpoint: str,
        auth: bool = False,
        **kwargs
    ) -> BenchmarkResult:
        """运行基准测试"""
        latencies = []
        successful = 0
        failed = 0
        
        headers = {}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def bounded_request(session):
            async with semaphore:
                return await self.make_request(session, method, endpoint, headers, **kwargs)
        
        connector = aiohttp.TCPConnector(limit=self.concurrency, limit_per_host=self.concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            # 先登录（如果需要认证）
            if auth:
                await self.login(session)
            
            # 预热
            print(f"  预热中...")
            warmup_tasks = [bounded_request(session) for _ in range(min(100, self.total_requests // 10))]
            await asyncio.gather(*warmup_tasks)
            
            # 正式测试
            print(f"  执行 {self.total_requests} 个请求 (并发: {self.concurrency})...")
            start_time = time.perf_counter()
            
            tasks = [bounded_request(session) for _ in range(self.total_requests)]
            results = await asyncio.gather(*tasks)
            
            total_time = time.perf_counter() - start_time
        
        for success, latency in results:
            latencies.append(latency)
            if success:
                successful += 1
            else:
                failed += 1
        
        # 计算统计数据
        sorted_latencies = sorted(latencies)
        
        return BenchmarkResult(
            endpoint=f"{method} {endpoint}",
            total_requests=self.total_requests,
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            requests_per_second=self.total_requests / total_time,
            avg_latency=statistics.mean(latencies) * 1000,
            min_latency=min(latencies) * 1000,
            max_latency=max(latencies) * 1000,
            p50_latency=sorted_latencies[int(len(sorted_latencies) * 0.5)] * 1000,
            p90_latency=sorted_latencies[int(len(sorted_latencies) * 0.9)] * 1000,
            p99_latency=sorted_latencies[int(len(sorted_latencies) * 0.99)] * 1000,
            latencies=latencies
        )
    
    def print_result(self, result: BenchmarkResult):
        """打印测试结果"""
        print(f"\n{'='*60}")
        print(f"端点: {result.endpoint}")
        print(f"{'='*60}")
        print(f"总请求数:      {result.total_requests}")
        print(f"成功请求:      {result.successful_requests}")
        print(f"失败请求:      {result.failed_requests}")
        print(f"总耗时:        {result.total_time:.2f} 秒")
        print(f"{'─'*60}")
        print(f"吞吐量:        {result.requests_per_second:.2f} req/s")
        print(f"{'─'*60}")
        print(f"延迟 (ms):")
        print(f"  平均:        {result.avg_latency:.2f}")
        print(f"  最小:        {result.min_latency:.2f}")
        print(f"  最大:        {result.max_latency:.2f}")
        print(f"  P50:         {result.p50_latency:.2f}")
        print(f"  P90:         {result.p90_latency:.2f}")
        print(f"  P99:         {result.p99_latency:.2f}")


async def main():
    parser = argparse.ArgumentParser(description="FastAPI 吞吐性能测试")
    parser.add_argument("--url", default="http://localhost:8000", help="服务地址")
    parser.add_argument("--requests", "-n", type=int, default=1000, help="总请求数")
    parser.add_argument("--concurrency", "-c", type=int, default=50, help="并发数")
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              FastAPI 吞吐性能测试                            ║
╠══════════════════════════════════════════════════════════════╣
║  服务地址:  {args.url:<48} ║
║  总请求数:  {args.requests:<48} ║
║  并发数:    {args.concurrency:<48} ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    benchmark = Benchmark(args.url, args.requests, args.concurrency)
    results = []
    
    # 测试 1: 健康检查（最简单的接口）
    print("\n[1/4] 测试健康检查接口 GET /health")
    result = await benchmark.run_benchmark("健康检查", "GET", "/health")
    benchmark.print_result(result)
    results.append(result)
    
    # 测试 2: API 根路径
    print("\n[2/4] 测试根路径 GET /")
    result = await benchmark.run_benchmark("根路径", "GET", "/")
    benchmark.print_result(result)
    results.append(result)
    
    # 测试 3: 登录接口
    print("\n[3/4] 测试登录接口 POST /auth/login")
    result = await benchmark.run_benchmark(
        "登录", "POST", "/auth/login",
        data={"username": "admin@example.com", "password": "admin123"}
    )
    benchmark.print_result(result)
    results.append(result)
    
    # 测试 4: 需要认证的接口
    print("\n[4/4] 测试认证接口 GET /auth/me")
    result = await benchmark.run_benchmark("获取当前用户", "GET", "/auth/me", auth=True)
    benchmark.print_result(result)
    results.append(result)
    
    # 汇总
    print(f"\n{'='*60}")
    print("测试汇总")
    print(f"{'='*60}")
    print(f"{'端点':<30} {'吞吐量 (req/s)':<15} {'P99 (ms)':<10}")
    print(f"{'─'*60}")
    for r in results:
        print(f"{r.endpoint:<30} {r.requests_per_second:<15.2f} {r.p99_latency:<10.2f}")
    
    avg_throughput = statistics.mean([r.requests_per_second for r in results])
    print(f"{'─'*60}")
    print(f"{'平均吞吐量':<30} {avg_throughput:<15.2f}")


if __name__ == "__main__":
    asyncio.run(main())
