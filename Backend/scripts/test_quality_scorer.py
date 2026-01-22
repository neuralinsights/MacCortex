#!/usr/bin/env python3
"""
MacCortex 测试质量评分器

评估测试的严格程度并提供改进建议。
"""

import re
import sys
from pathlib import Path
from typing import Dict, List


class TestQualityScorer:
    """测试质量评分器"""

    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.test_files = list(test_dir.rglob("test_*.py"))
        self.total_content = ""

        for file in self.test_files:
            self.total_content += file.read_text()

    def score(self) -> Dict:
        """
        评分标准（总分 100）：
        - 基础测试：20 分
        - 边缘情况：30 分
        - 错误处理：20 分
        - 集成测试：15 分
        - 真实场景：15 分
        """
        scores = {
            "basic": self._check_basic_tests(),
            "edge_cases": self._check_edge_cases(),
            "error_handling": self._check_error_handling(),
            "integration": self._check_integration(),
            "real_vs_mock": self._check_real_scenarios(),
        }

        total = sum(scores.values())

        return {
            "total": total,
            "breakdown": scores,
            "pass": total >= 80,
            "suggestions": self._generate_suggestions(scores)
        }

    def _check_basic_tests(self) -> int:
        """检查基础测试覆盖（20 分）"""
        # 检查测试函数数量
        test_functions = re.findall(r"def test_\w+\(", self.total_content)
        test_count = len(test_functions)

        if test_count >= 20:
            return 20
        elif test_count >= 10:
            return 15
        elif test_count >= 5:
            return 10
        else:
            return 5

    def _check_edge_cases(self) -> int:
        """检查边缘情况覆盖（30 分）"""
        patterns = {
            r"test.*invalid": "无效输入测试",
            r"test.*empty": "空数据测试",
            r"test.*null|test.*none": "空值测试",
            r"test.*boundary": "边界条件测试",
            r"test.*overflow": "溢出测试",
            r"test.*edge": "边缘情况测试",
            r"test.*error": "错误场景测试",
        }

        found_patterns = []
        for pattern, name in patterns.items():
            if re.search(pattern, self.total_content, re.I):
                found_patterns.append(name)

        # 每个模式 5 分，最多 30 分
        return min(len(found_patterns) * 5, 30)

    def _check_error_handling(self) -> int:
        """检查错误处理测试（20 分）"""
        score = 0

        # pytest.raises 用法（10 分）
        if "pytest.raises" in self.total_content:
            raises_count = self.total_content.count("pytest.raises")
            score += min(raises_count * 2, 10)

        # Exception 测试（5 分）
        if re.search(r"(Exception|Error)\b", self.total_content):
            score += 5

        # try-except 测试（5 分）
        if "try:" in self.total_content and "except" in self.total_content:
            score += 5

        return min(score, 20)

    def _check_integration(self) -> int:
        """检查集成测试（15 分）"""
        score = 0

        # 异步集成测试（8 分）
        if "@pytest.mark.asyncio" in self.total_content:
            async_tests = self.total_content.count("@pytest.mark.asyncio")
            score += min(async_tests, 8)

        # 多模块集成（7 分）
        imports = re.findall(r"from src\.(\w+)", self.total_content)
        unique_modules = len(set(imports))
        if unique_modules >= 3:
            score += 7
        elif unique_modules >= 2:
            score += 4

        return min(score, 15)

    def _check_real_scenarios(self) -> int:
        """检查真实场景 vs Mock（15 分）"""
        mock_count = self.total_content.count("Mock") + self.total_content.count("mock")
        real_count = self.total_content.count("await ") + self.total_content.count("async def")

        # 真实文件操作
        real_file_ops = self.total_content.count("Path(") + self.total_content.count("open(")

        # 计算真实场景占比
        total_ops = mock_count + real_count + real_file_ops
        if total_ops == 0:
            return 0

        real_ratio = (real_count + real_file_ops) / total_ops

        if real_ratio >= 0.5:
            return 15  # 真实场景 ≥ 50%
        elif real_ratio >= 0.3:
            return 10  # 真实场景 ≥ 30%
        elif real_ratio > 0:
            return 5   # 有真实场景
        else:
            return 0   # 全是 Mock

    def _generate_suggestions(self, scores: Dict[str, int]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        if scores["basic"] < 20:
            suggestions.append("📝 增加基础测试数量（当前不足 20 个测试函数）")

        if scores["edge_cases"] < 20:
            missing = []
            if "invalid" not in self.total_content.lower():
                missing.append("无效输入")
            if "empty" not in self.total_content.lower():
                missing.append("空数据")
            if "boundary" not in self.total_content.lower():
                missing.append("边界条件")

            if missing:
                suggestions.append(f"🔍 添加边缘情况测试：{', '.join(missing)}")

        if scores["error_handling"] < 15:
            if "pytest.raises" not in self.total_content:
                suggestions.append("⚠️  使用 pytest.raises 测试异常")

        if scores["integration"] < 10:
            suggestions.append("🔗 增加集成测试（跨模块测试）")

        if scores["real_vs_mock"] < 10:
            suggestions.append("🎯 减少 Mock，增加真实场景测试")

        return suggestions

    def print_report(self):
        """打印评分报告"""
        result = self.score()

        print()
        print("=" * 60)
        print("🤖 Testing Agent - 测试质量评分报告")
        print("=" * 60)
        print()

        # 详细评分
        print("📊 评分详情：")
        print("-" * 60)

        breakdown = result["breakdown"]
        max_scores = {
            "basic": 20,
            "edge_cases": 30,
            "error_handling": 20,
            "integration": 15,
            "real_vs_mock": 15,
        }

        labels = {
            "basic": "基础测试",
            "edge_cases": "边缘情况",
            "error_handling": "错误处理",
            "integration": "集成测试",
            "real_vs_mock": "真实场景",
        }

        for key, label in labels.items():
            score = breakdown[key]
            max_score = max_scores[key]
            percentage = (score / max_score) * 100

            # 状态标记
            if percentage >= 80:
                status = "✅"
            elif percentage >= 60:
                status = "⚠️ "
            else:
                status = "❌"

            print(f"{status} {label:12} {score:2}/{max_score:2} ({percentage:5.1f}%)")

        print("-" * 60)

        # 总分
        total = result["total"]
        if result["pass"]:
            status = "✅ 通过"
            emoji = "🎉"
        else:
            status = "❌ 未通过"
            emoji = "⚠️ "

        print(f"\n{emoji} 总分：{total}/100 - {status}（需要 ≥ 80）")

        # 改进建议
        if result["suggestions"]:
            print()
            print("💡 改进建议：")
            print("-" * 60)
            for i, suggestion in enumerate(result["suggestions"], 1):
                print(f"{i}. {suggestion}")

        print()
        print("=" * 60)
        print()

        # 返回状态码
        return 0 if result["pass"] else 1


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_quality_scorer.py <tests_directory>")
        print("示例: python test_quality_scorer.py tests/")
        sys.exit(1)

    test_dir = Path(sys.argv[1])
    if not test_dir.exists():
        print(f"❌ 测试目录不存在：{test_dir}")
        sys.exit(1)

    scorer = TestQualityScorer(test_dir)
    exit_code = scorer.print_report()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
