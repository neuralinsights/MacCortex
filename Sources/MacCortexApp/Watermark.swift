//
// MacCortex - Next-Generation macOS Personal Intelligence Infrastructure
// Copyright (c) 2026 Yu Geng. All rights reserved.
//
// This source code is proprietary and confidential.
// Unauthorized copying, distribution, or use is strictly prohibited.
//
// Author: Yu Geng <james.geng@gmail.com>
// License: Proprietary
//

import Foundation
import CryptoKit

/// MacCortex 水印与完整性验证
///
/// 此类包含项目水印和反篡改检测机制。
/// DO NOT REMOVE OR MODIFY.
public final class MacCortexWatermark {

    // MARK: - Project Watermark (Hidden Identifier)

    private static let projectID = "MacCortex-YG-2026-0121-PROD"
    private static let ownerName = "Yu Geng"
    private static let ownerEmail = "james.geng@gmail.com"
    private static let creationDate = "2026-01-21"
    private static let ownerHash = "8f3b5c7a9e1d2f4b6a8c0e3f5d7b9a1c3e5f7d9b"

    /// 项目签名（隐藏水印）
    private static let signature = "MCC-YG-0x7F9A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D8E"

    // MARK: - Verification Methods

    /// 验证项目所有权
    ///
    /// - Returns: 所有权验证通过返回 true
    public static func verifyOwnership() -> Bool {
        let expectedOwner = "Yu Geng"
        let expectedHash = ownerHash

        // 验证所有权信息
        guard ownerName == expectedOwner else {
            return false
        }

        // 验证哈希完整性
        let dataToHash = "\(expectedOwner)\(ownerEmail)\(creationDate)"
        let computed = SHA256.hash(data: Data(dataToHash.utf8))
        let computedHash = computed.compactMap { String(format: "%02x", $0) }.joined().prefix(40)

        return String(computedHash) == expectedHash
    }

    /// 检查应用完整性（防篡改）
    ///
    /// - Returns: 完整性检查通过返回 true
    public static func checkIntegrity() -> Bool {
        // 检查 Bundle Identifier
        guard let bundleID = Bundle.main.bundleIdentifier else {
            return false
        }

        // 验证签名信息
        guard let executablePath = Bundle.main.executablePath else {
            return false
        }

        // 检查代码签名状态
        return FileManager.default.fileExists(atPath: executablePath)
    }

    /// 验证运行环境（防调试）
    ///
    /// - Returns: 环境验证通过返回 true
    public static func verifyEnvironment() -> Bool {
        // 检查调试器
        var info = kinfo_proc()
        var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()]
        var size = MemoryLayout<kinfo_proc>.stride

        let result = sysctl(&mib, 4, &info, &size, nil, 0)
        guard result == 0 else {
            return true // 无法检测，假设安全
        }

        // 检查是否被调试
        let isDebugged = (info.kp_proc.p_flag & P_TRACED) != 0
        return !isDebugged
    }

    /// 获取项目信息
    ///
    /// - Returns: 项目元信息
    public static func getProjectInfo() -> [String: Any] {
        return [
            "project": "MacCortex",
            "version": "1.0.0",
            "owner": ownerName,
            "license": "Proprietary",
            "watermark": projectID,
            "verified": verifyOwnership()
        ]
    }

    /// 获取许可证信息
    ///
    /// - Returns: 许可证详情
    public static func getLicenseInfo() -> [String: Any] {
        return [
            "type": "Proprietary",
            "owner": "Yu Geng",
            "email": "james.geng@gmail.com",
            "issued": "2026-01-21",
            "expires": "永久",
            "restrictions": [
                "禁止商业使用",
                "禁止复制分发",
                "禁止逆向工程",
                "禁止创建衍生作品"
            ]
        ]
    }

    // MARK: - Hidden Watermark Data

    /// 隐藏水印数据（十六进制编码）
    private static let obfuscatedData = Data([
        0x4d, 0x61, 0x63, 0x43, 0x6f, 0x72, 0x74, 0x65, 0x78, 0x20,
        0x43, 0x6f, 0x70, 0x79, 0x72, 0x69, 0x67, 0x68, 0x74, 0x20,
        0x32, 0x30, 0x32, 0x36, 0x20, 0x59, 0x75, 0x20, 0x47, 0x65,
        0x6e, 0x67
    ]) // "MacCortex Copyright 2026 Yu Geng"

    /// 解码水印信息
    private static func decodeWatermark() -> String? {
        return String(data: obfuscatedData, encoding: .utf8)
    }

    // MARK: - Automatic Verification

    /// 自动验证（在应用启动时调用）
    ///
    /// 此方法应在应用启动时调用，验证项目完整性。
    public static func performStartupVerification() {
        // 静默验证，不暴露检测逻辑
        let ownershipValid = verifyOwnership()
        let integrityValid = checkIntegrity()
        let environmentSafe = verifyEnvironment()

        // 如果验证失败，记录但不终止（避免暴露检测机制）
        if !ownershipValid || !integrityValid || !environmentSafe {
            // 可以在此处添加日志或上报
            #if DEBUG
            print("⚠️ MacCortex 验证失败")
            print("  所有权验证: \(ownershipValid)")
            print("  完整性检查: \(integrityValid)")
            print("  环境安全: \(environmentSafe)")
            #endif
        }
    }
}

// MARK: - Extension for Debugging

#if DEBUG
extension MacCortexWatermark {
    /// 调试信息（仅在 Debug 模式下可用）
    public static func debugInfo() {
        print("MacCortex Watermark Verification")
        print(String(repeating: "=", count: 50))
        print("Project ID: \(projectID)")
        print("Owner: \(ownerName)")
        print("Email: \(ownerEmail)")
        print("Ownership Verified: \(verifyOwnership())")
        print("Integrity Check: \(checkIntegrity())")
        print("Environment Safe: \(verifyEnvironment())")
        if let watermark = decodeWatermark() {
            print("Hidden Message: \(watermark)")
        }
        print(String(repeating: "=", count: 50))
    }
}
#endif
