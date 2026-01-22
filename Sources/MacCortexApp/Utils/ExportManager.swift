//
//  ExportManager.swift
//  MacCortex
//
//  Phase 3 Week 4 Day 3-4 - 导出管理器
//  Created on 2026-01-22
//

import Foundation
import AppKit

/// 导出格式
enum ExportFormat: String, CaseIterable, Identifiable {
    case txt = "txt"
    case pdf = "pdf"
    case docx = "docx"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .txt: return "纯文本 (.txt)"
        case .pdf: return "PDF 文档 (.pdf)"
        case .docx: return "Word 文档 (.docx)"
        }
    }

    var icon: String {
        switch self {
        case .txt: return "doc.text"
        case .pdf: return "doc.richtext"
        case .docx: return "doc"
        }
    }
}

/// 导出布局
enum ExportLayout: String, CaseIterable, Identifiable {
    case sourceOnly = "source_only"
    case translationOnly = "translation_only"
    case sideBySide = "side_by_side"
    case sequential = "sequential"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .sourceOnly: return "仅原文"
        case .translationOnly: return "仅译文"
        case .sideBySide: return "左右对照"
        case .sequential: return "上下对照"
        }
    }

    var description: String {
        switch self {
        case .sourceOnly: return "仅导出原文内容"
        case .translationOnly: return "仅导出翻译结果"
        case .sideBySide: return "原文和译文左右并排"
        case .sequential: return "原文和译文上下排列"
        }
    }
}

/// 导出配置
struct ExportOptions {
    var format: ExportFormat
    var layout: ExportLayout
    var includeMetadata: Bool
    var includeTimestamp: Bool

    static let `default` = ExportOptions(
        format: .txt,
        layout: .sequential,
        includeMetadata: true,
        includeTimestamp: true
    )
}

/// 导出管理器（单例）
class ExportManager {
    static let shared = ExportManager()

    private init() {}

    /// 导出批量翻译结果
    ///
    /// - Parameters:
    ///   - items: 批量翻译项数组
    ///   - options: 导出配置
    ///   - url: 保存路径
    /// - Throws: ExportError
    func export(items: [BatchItem], options: ExportOptions, to url: URL) throws {
        // 过滤已完成的项
        let completedItems = items.filter { $0.status == .completed }

        guard !completedItems.isEmpty else {
            throw ExportError.noCompletedItems
        }

        switch options.format {
        case .txt:
            try exportToText(items: completedItems, options: options, to: url)
        case .pdf:
            try exportToPDF(items: completedItems, options: options, to: url)
        case .docx:
            try exportToDocx(items: completedItems, options: options, to: url)
        }

        // 导出成功后发送通知
        Task { @MainActor in
            await NotificationManager.shared.sendExportCompletedNotification(
                format: options.format,
                itemCount: completedItems.count,
                filePath: url.path
            )
        }
    }

    // MARK: - Text Export

    /// 导出为纯文本
    private func exportToText(items: [BatchItem], options: ExportOptions, to url: URL) throws {
        var content = ""

        // 添加元数据
        if options.includeMetadata {
            content += generateMetadata(itemCount: items.count, timestamp: options.includeTimestamp)
            content += "\n" + String(repeating: "=", count: 80) + "\n\n"
        }

        // 添加每个文件的内容
        for (index, item) in items.enumerated() {
            content += "[\(index + 1)] \(item.fileName)\n"
            content += String(repeating: "-", count: 80) + "\n\n"

            switch options.layout {
            case .sourceOnly:
                content += item.sourceText ?? ""

            case .translationOnly:
                content += item.translatedText ?? ""

            case .sideBySide:
                content += formatSideBySide(
                    source: item.sourceText ?? "",
                    translation: item.translatedText ?? ""
                )

            case .sequential:
                content += "【原文】\n"
                content += item.sourceText ?? ""
                content += "\n\n【译文】\n"
                content += item.translatedText ?? ""
            }

            content += "\n\n"
        }

        // 保存文件
        do {
            try content.write(to: url, atomically: true, encoding: .utf8)
        } catch {
            throw ExportError.writeFailed(error.localizedDescription)
        }
    }

    // MARK: - PDF Export

    /// 导出为 PDF
    private func exportToPDF(items: [BatchItem], options: ExportOptions, to url: URL) throws {
        // 生成 PDF 内容
        var content = ""

        // 添加元数据
        if options.includeMetadata {
            content += generateMetadata(itemCount: items.count, timestamp: options.includeTimestamp)
            content += "\n" + String(repeating: "=", count: 80) + "\n\n"
        }

        // 添加每个文件的内容
        for (index, item) in items.enumerated() {
            content += "[\(index + 1)] \(item.fileName)\n"
            content += String(repeating: "-", count: 80) + "\n\n"

            switch options.layout {
            case .sourceOnly:
                content += item.sourceText ?? ""

            case .translationOnly:
                content += item.translatedText ?? ""

            case .sideBySide:
                // PDF 不支持真正的左右布局，使用上下对照
                content += "【原文】\n"
                content += item.sourceText ?? ""
                content += "\n\n【译文】\n"
                content += item.translatedText ?? ""

            case .sequential:
                content += "【原文】\n"
                content += item.sourceText ?? ""
                content += "\n\n【译文】\n"
                content += item.translatedText ?? ""
            }

            content += "\n\n"
        }

        // 使用 PDFGenerator 生成 PDF
        try PDFGenerator.shared.generate(content: content, to: url)
    }

    // MARK: - DOCX Export

    /// 导出为 Word 文档
    ///
    /// 注意：使用 NSAttributedString 简化方案
    /// 完整的 DOCX 导出需要第三方库（如 Python-docx + Bridge）
    private func exportToDocx(items: [BatchItem], options: ExportOptions, to url: URL) throws {
        // 生成富文本内容
        let attributedString = NSMutableAttributedString()

        // 默认字体
        let bodyFont = NSFont.systemFont(ofSize: 12)
        let titleFont = NSFont.boldSystemFont(ofSize: 14)
        let headerFont = NSFont.boldSystemFont(ofSize: 16)

        // 添加元数据
        if options.includeMetadata {
            let metadata = generateMetadata(itemCount: items.count, timestamp: options.includeTimestamp)
            let metadataAttr = NSAttributedString(
                string: metadata + "\n\n",
                attributes: [.font: bodyFont, .foregroundColor: NSColor.secondaryLabelColor]
            )
            attributedString.append(metadataAttr)
        }

        // 添加每个文件的内容
        for (index, item) in items.enumerated() {
            // 文件名标题
            let title = NSAttributedString(
                string: "[\(index + 1)] \(item.fileName)\n",
                attributes: [.font: titleFont, .foregroundColor: NSColor.labelColor]
            )
            attributedString.append(title)

            // 分隔线
            let separator = NSAttributedString(
                string: String(repeating: "-", count: 40) + "\n\n",
                attributes: [.font: bodyFont, .foregroundColor: NSColor.separatorColor]
            )
            attributedString.append(separator)

            // 内容
            switch options.layout {
            case .sourceOnly:
                let sourceAttr = NSAttributedString(
                    string: (item.sourceText ?? "") + "\n\n",
                    attributes: [.font: bodyFont]
                )
                attributedString.append(sourceAttr)

            case .translationOnly:
                let translationAttr = NSAttributedString(
                    string: (item.translatedText ?? "") + "\n\n",
                    attributes: [.font: bodyFont]
                )
                attributedString.append(translationAttr)

            case .sideBySide, .sequential:
                // 原文标题
                let sourceTitle = NSAttributedString(
                    string: "【原文】\n",
                    attributes: [.font: headerFont, .foregroundColor: NSColor.systemBlue]
                )
                attributedString.append(sourceTitle)

                // 原文内容
                let sourceAttr = NSAttributedString(
                    string: (item.sourceText ?? "") + "\n\n",
                    attributes: [.font: bodyFont]
                )
                attributedString.append(sourceAttr)

                // 译文标题
                let translationTitle = NSAttributedString(
                    string: "【译文】\n",
                    attributes: [.font: headerFont, .foregroundColor: NSColor.systemGreen]
                )
                attributedString.append(translationTitle)

                // 译文内容
                let translationAttr = NSAttributedString(
                    string: (item.translatedText ?? "") + "\n\n",
                    attributes: [.font: bodyFont]
                )
                attributedString.append(translationAttr)
            }
        }

        // 保存为 RTF（DOCX 需要第三方库，使用 RTF 作为替代）
        let data = try attributedString.data(
            from: NSRange(location: 0, length: attributedString.length),
            documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf]
        )
        try data.write(to: url)
    }

    // MARK: - Helper Methods

    /// 生成元数据
    private func generateMetadata(itemCount: Int, timestamp: Bool) -> String {
        var metadata = "MacCortex 批量翻译导出\n"
        metadata += "文件数量：\(itemCount)\n"

        if timestamp {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
            metadata += "导出时间：\(formatter.string(from: Date()))\n"
        }

        return metadata
    }

    /// 格式化左右对照（纯文本）
    ///
    /// 注意：纯文本不支持真正的左右布局，使用分栏模拟
    private func formatSideBySide(source: String, translation: String) -> String {
        let sourceLines = source.components(separatedBy: .newlines)
        let translationLines = translation.components(separatedBy: .newlines)
        let maxLines = max(sourceLines.count, translationLines.count)

        var result = ""
        let columnWidth = 40

        result += "【原文】".padding(toLength: columnWidth, withPad: " ", startingAt: 0)
        result += " | 【译文】\n"
        result += String(repeating: "-", count: columnWidth) + "-+-"
        result += String(repeating: "-", count: columnWidth) + "\n"

        for i in 0..<maxLines {
            let sourceLine = i < sourceLines.count ? sourceLines[i] : ""
            let translationLine = i < translationLines.count ? translationLines[i] : ""

            result += sourceLine.padding(toLength: columnWidth, withPad: " ", startingAt: 0)
            result += " | "
            result += translationLine
            result += "\n"
        }

        return result
    }
}

/// 导出错误
enum ExportError: LocalizedError {
    case noCompletedItems
    case writeFailed(String)
    case pdfGenerationFailed(String)
    case docxGenerationFailed(String)

    var errorDescription: String? {
        switch self {
        case .noCompletedItems:
            return "没有已完成的翻译项"
        case .writeFailed(let detail):
            return "文件写入失败: \(detail)"
        case .pdfGenerationFailed(let detail):
            return "PDF 生成失败: \(detail)"
        case .docxGenerationFailed(let detail):
            return "DOCX 生成失败: \(detail)"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .noCompletedItems:
            return "请先完成至少一个翻译任务"
        case .writeFailed:
            return "请检查文件路径和权限"
        case .pdfGenerationFailed, .docxGenerationFailed:
            return "请尝试导出为纯文本格式"
        }
    }
}
