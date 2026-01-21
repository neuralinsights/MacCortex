//
//  PDFGenerator.swift
//  MacCortex
//
//  Phase 3 Week 4 Day 3-4 - PDF 生成工具
//  Created on 2026-01-22
//

import Foundation
import AppKit
import PDFKit

/// PDF 生成器（单例）
class PDFGenerator {
    static let shared = PDFGenerator()

    private init() {}

    /// 生成 PDF 文档
    ///
    /// - Parameters:
    ///   - content: 文本内容
    ///   - url: 保存路径
    /// - Throws: ExportError
    func generate(content: String, to url: URL) throws {
        // 创建 NSAttributedString
        let attributedString = createAttributedString(from: content)

        // 创建 PDF 数据
        guard let pdfData = createPDFData(from: attributedString) else {
            throw ExportError.pdfGenerationFailed("无法生成 PDF 数据")
        }

        // 保存文件
        do {
            try pdfData.write(to: url)
        } catch {
            throw ExportError.writeFailed(error.localizedDescription)
        }
    }

    // MARK: - Private Methods

    /// 创建富文本字符串
    private func createAttributedString(from content: String) -> NSAttributedString {
        let attributedString = NSMutableAttributedString()

        // 分段处理（识别标题和正文）
        let lines = content.components(separatedBy: .newlines)

        for line in lines {
            let attributes: [NSAttributedString.Key: Any]

            if line.hasPrefix("[") && line.contains("]") {
                // 文件标题
                attributes = [
                    .font: NSFont.boldSystemFont(ofSize: 14),
                    .foregroundColor: NSColor.labelColor
                ]
            } else if line.hasPrefix("【") && line.hasSuffix("】") {
                // 章节标题
                attributes = [
                    .font: NSFont.boldSystemFont(ofSize: 13),
                    .foregroundColor: NSColor.systemBlue
                ]
            } else if line.starts(with: "MacCortex") {
                // 元数据
                attributes = [
                    .font: NSFont.systemFont(ofSize: 10),
                    .foregroundColor: NSColor.secondaryLabelColor
                ]
            } else {
                // 正文
                attributes = [
                    .font: NSFont.systemFont(ofSize: 11),
                    .foregroundColor: NSColor.labelColor
                ]
            }

            let lineAttr = NSAttributedString(
                string: line + "\n",
                attributes: attributes
            )
            attributedString.append(lineAttr)
        }

        return attributedString
    }

    /// 创建 PDF 数据
    private func createPDFData(from attributedString: NSAttributedString) -> Data? {
        // 设置 PDF 页面大小（A4）
        let pageSize = CGSize(width: 595, height: 842)  // A4: 210mm x 297mm
        let margin: CGFloat = 50

        // 创建 PDF 上下文
        let pdfData = NSMutableData()
        guard let consumer = CGDataConsumer(data: pdfData),
              let context = CGContext(consumer: consumer, mediaBox: nil, nil) else {
            return nil
        }

        // 开始 PDF 文档
        context.beginPDFPage(nil)

        // 设置绘制区域
        let drawRect = CGRect(
            x: margin,
            y: margin,
            width: pageSize.width - 2 * margin,
            height: pageSize.height - 2 * margin
        )

        // 绘制文本
        let framesetter = CTFramesetterCreateWithAttributedString(attributedString)
        let path = CGPath(rect: drawRect, transform: nil)
        let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: 0, length: 0), path, nil)

        // 翻转坐标系（PDF 坐标系原点在左下角）
        context.textMatrix = .identity
        context.translateBy(x: 0, y: pageSize.height)
        context.scaleBy(x: 1, y: -1)

        CTFrameDraw(frame, context)

        // 结束 PDF 页面
        context.endPDFPage()
        context.closePDF()

        return pdfData as Data
    }
}
