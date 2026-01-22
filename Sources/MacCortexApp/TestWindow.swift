//
// TestWindow.swift
// Week 5 诊断 - AppKit 原生窗口测试
//

import Cocoa
import SwiftUI

class TestWindowController: NSWindowController {
    convenience init() {
        // 强制在主屏幕中心创建窗口
        guard let mainScreen = NSScreen.main else {
            self.init(window: nil)
            return
        }

        let screenFrame = mainScreen.visibleFrame
        let windowWidth: CGFloat = 800
        let windowHeight: CGFloat = 600
        let windowX = screenFrame.midX - windowWidth / 2
        let windowY = screenFrame.midY - windowHeight / 2

        let window = NSWindow(
            contentRect: NSRect(x: windowX, y: windowY, width: windowWidth, height: windowHeight),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )

        window.title = "✅ MacCortex 已启动"
        window.backgroundColor = .systemRed
        window.level = .floating  // 置顶显示
        window.isOpaque = true
        window.hasShadow = true

        // 创建一个简单的label
        let label = NSTextField(labelWithString: "🎉 窗口渲染成功！\n\nMacCortex Week 5 验收系统")
        label.font = NSFont.systemFont(ofSize: 48, weight: .bold)
        label.textColor = .white
        label.alignment = .center
        label.frame = NSRect(x: 50, y: 200, width: 700, height: 200)

        window.contentView?.addSubview(label)

        // 强制显示在主屏幕
        window.setFrameOrigin(NSPoint(x: windowX, y: windowY))
        window.makeKeyAndOrderFront(nil)
        window.orderFrontRegardless()

        self.init(window: window)
    }
}
