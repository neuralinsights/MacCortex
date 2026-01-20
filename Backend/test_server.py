"""
快速测试 FastAPI 服务器
"""

import sys
import asyncio
from src.main import app

async def test_health():
    """测试健康检查端点"""
    print("🧪 测试 FastAPI 服务器...")

    # 简单测试：检查 app 是否可以实例化
    assert app is not None, "❌ FastAPI app 创建失败"
    print("✅ FastAPI app 创建成功")

    # 检查路由
    routes = [route.path for route in app.routes]
    print(f"✅ 已注册 {len(routes)} 个路由:")
    for route in routes:
        print(f"   - {route}")

    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_health())
        if result:
            print("\n🎉 FastAPI 服务器基础测试通过！")
            print("\n下一步：")
            print("  1. 启动服务器: python src/main.py")
            print("  2. 访问文档: http://localhost:8000/docs")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
