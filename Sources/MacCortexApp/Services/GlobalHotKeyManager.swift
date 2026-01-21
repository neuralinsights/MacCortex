//
//  GlobalHotKeyManager.swift
//  MacCortex
//
//  Phase 3 Week 3 Day 5 - 全局快捷键管理
//  Created on 2026-01-22
//

import Foundation
import AppKit
import Carbon

/// 全局快捷键管理器
///
/// 使用 Carbon API 注册全局快捷键：
/// - Cmd+Shift+T: 显示/隐藏悬浮翻译面板
/// - 支持动态注册/注销
/// - 支持自定义快捷键（未来扩展）
@MainActor
class GlobalHotKeyManager: ObservableObject {
    static let shared = GlobalHotKeyManager()

    // MARK: - Properties

    /// 是否启用全局快捷键
    @Published var isEnabled: Bool = true {
        didSet {
            if isEnabled {
                registerHotKeys()
            } else {
                unregisterHotKeys()
            }
        }
    }

    /// 当前注册的热键引用
    private var hotKeyRef: EventHotKeyRef?

    /// 热键 ID
    private let hotKeyID = EventHotKeyID(signature: FourCharCode(truncating: "MCTX" as NSString), id: 1)

    // MARK: - Initialization

    private init() {
        // 初始化时不自动注册，等待 App 启动完成
    }

    // MARK: - Public Methods

    /// 注册全局快捷键
    func registerHotKeys() {
        guard hotKeyRef == nil else {
            print("[GlobalHotKeyManager] 快捷键已注册，跳过")
            return
        }

        // 1. 安装事件处理器
        var eventHandler = EventHandlerUPP { nextHandler, theEvent, userData in
            GlobalHotKeyManager.handleHotKeyEvent(nextHandler, theEvent, userData)
        }

        var eventSpec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard),
                                      eventKind: OSType(kEventHotKeyPressed))

        InstallEventHandler(
            GetApplicationEventTarget(),
            eventHandler,
            1,
            &eventSpec,
            nil,
            nil
        )

        // 2. 注册 Cmd+Shift+T
        let keyCode = kVK_ANSI_T  // T 键
        let modifiers = UInt32(cmdKey | shiftKey)  // Cmd+Shift

        let status = RegisterEventHotKey(
            UInt32(keyCode),
            modifiers,
            hotKeyID,
            GetApplicationEventTarget(),
            0,
            &hotKeyRef
        )

        if status == noErr {
            print("[GlobalHotKeyManager] ✅ 全局快捷键注册成功: Cmd+Shift+T")
        } else {
            print("[GlobalHotKeyManager] ❌ 全局快捷键注册失败: \(status)")
        }
    }

    /// 注销全局快捷键
    func unregisterHotKeys() {
        guard let hotKey = hotKeyRef else {
            return
        }

        let status = UnregisterEventHotKey(hotKey)
        if status == noErr {
            print("[GlobalHotKeyManager] ✅ 全局快捷键注销成功")
        } else {
            print("[GlobalHotKeyManager] ❌ 全局快捷键注销失败: \(status)")
        }

        hotKeyRef = nil
    }

    // MARK: - Private Methods

    /// 处理热键事件
    private static func handleHotKeyEvent(
        _ nextHandler: EventHandlerCallRef?,
        _ theEvent: EventRef?,
        _ userData: UnsafeMutableRawPointer?
    ) -> OSStatus {
        // 解析事件 ID
        var hotKeyID = EventHotKeyID()
        let status = GetEventParameter(
            theEvent,
            EventParamName(kEventParamDirectObject),
            EventParamType(typeEventHotKeyID),
            nil,
            MemoryLayout<EventHotKeyID>.size,
            nil,
            &hotKeyID
        )

        guard status == noErr else {
            return status
        }

        // 验证是否是我们的热键
        let signature = String(describing: hotKeyID.signature)
        if signature == "MCTX" && hotKeyID.id == 1 {
            // 触发浮动面板
            Task { @MainActor in
                FloatingPanelManager.shared.togglePanel()
            }
        }

        return noErr
    }

    // MARK: - Cleanup

    deinit {
        unregisterHotKeys()
    }
}

// MARK: - Carbon Key Codes

extension GlobalHotKeyManager {
    /// 常用按键代码
    enum KeyCode: Int {
        case t = 0x11  // kVK_ANSI_T
        case space = 0x31  // kVK_Space
        case escape = 0x35  // kVK_Escape
        case enter = 0x24  // kVK_Return
    }
}
