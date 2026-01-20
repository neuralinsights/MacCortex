// swift-tools-version: 5.9
// MacCortex - Swift Package Manager 配置
// Phase 0.5
// 创建时间：2026-01-20

import PackageDescription

let package = Package(
    name: "MacCortex",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "MacCortex",
            targets: ["MacCortexApp"]
        ),
    ],
    dependencies: [
        // Sparkle 2 - 自动更新框架（Phase 0.5 Day 10）
        .package(url: "https://github.com/sparkle-project/Sparkle", from: "2.5.0"),
        
        // FullDiskAccess - 权限检测（Phase 0.5 Day 6-7）
        // 注意：这是一个单文件包，我们会直接集成源码
    ],
    targets: [
        // 主应用目标
        .executableTarget(
            name: "MacCortexApp",
            dependencies: [
                "PermissionsKit",
                .product(name: "Sparkle", package: "Sparkle"),
            ],
            path: "Sources/MacCortexApp",
            resources: [
                .process("Resources")
            ]
        ),
        
        // 权限管理模块
        .target(
            name: "PermissionsKit",
            dependencies: [],
            path: "Sources/PermissionsKit"
        ),
        
        // Python 桥接模块（Phase 1+）
        .target(
            name: "PythonBridge",
            dependencies: [],
            path: "Sources/PythonBridge"
        ),
        
        // 测试目标
        .testTarget(
            name: "PermissionsKitTests",
            dependencies: [
                "PermissionsKit"
            ],
            path: "Tests/PermissionsKitTests"
        ),
    ]
)
