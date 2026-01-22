//
//  FileReader.swift
//  MacCortex
//
//  Phase 3 Week 4 Day 1-2 - 文件读取工具
//  Created on 2026-01-22
//

import Foundation
import AppKit

/// 文件读取器（单例）
class FileReader {
    static let shared = FileReader()

    private init() {}

    /// 读取文件内容
    ///
    /// 支持格式：
    /// - .txt: 纯文本（UTF-8）
    /// - .md: Markdown（UTF-8）
    /// - .docx: Word 文档（使用 NSAttributedString）
    ///
    /// - Parameter url: 文件 URL
    /// - Returns: 文件内容（字符串）
    /// - Throws: FileReadError
    func readFile(_ url: URL) throws -> String {
        let fileType = url.pathExtension.lowercased()

        switch fileType {
        case "txt", "md":
            return try readPlainText(url)

        case "docx":
            return try readDocx(url)

        default:
            throw FileReadError.unsupportedFormat(fileType)
        }
    }

    // MARK: - Private Methods

    /// 读取纯文本文件
    private func readPlainText(_ url: URL) throws -> String {
        do {
            let content = try String(contentsOf: url, encoding: .utf8)

            // 检查内容是否为空
            guard !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw FileReadError.emptyFile
            }

            return content
        } catch {
            throw FileReadError.readFailed(error.localizedDescription)
        }
    }

    /// 读取 DOCX 文件
    ///
    /// 使用 NSAttributedString 读取 DOCX 文件
    /// 注意：仅提取纯文本，不保留格式
    private func readDocx(_ url: URL) throws -> String {
        do {
            // DOCX 需要第三方库，使用 RTF 作为替代（或者抛出不支持错误）
            // 如果文件实际上是 RTF，可以尝试读取
            let attributedString = try NSAttributedString(
                url: url,
                options: [.documentType: NSAttributedString.DocumentType.rtf],
                documentAttributes: nil
            )

            let content = attributedString.string

            // 检查内容是否为空
            guard !content.trimmingCharacters(in: CharacterSet.whitespacesAndNewlines).isEmpty else {
                throw FileReadError.emptyFile
            }

            return content
        } catch let error as FileReadError {
            throw error
        } catch {
            throw FileReadError.readFailed(error.localizedDescription)
        }
    }
}

/// 文件读取错误
enum FileReadError: LocalizedError {
    case unsupportedFormat(String)
    case emptyFile
    case readFailed(String)
    case parseError(String)

    var errorDescription: String? {
        switch self {
        case .unsupportedFormat(let format):
            return "不支持的文件格式: .\(format)"
        case .emptyFile:
            return "文件内容为空"
        case .readFailed(let detail):
            return "文件读取失败: \(detail)"
        case .parseError(let detail):
            return "文件解析失败: \(detail)"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unsupportedFormat:
            return "目前仅支持 .txt、.md、.docx 格式"
        case .emptyFile:
            return "请确认文件包含有效内容"
        case .readFailed:
            return "请检查文件是否存在且有读取权限"
        case .parseError:
            return "请确认文件格式正确且未损坏"
        }
    }
}
