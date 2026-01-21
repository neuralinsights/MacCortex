//
//  ExportOptionsView.swift
//  MacCortex
//
//  Phase 3 Week 4 Day 3-4 - 导出选项界面
//  Created on 2026-01-22
//

import SwiftUI

/// 导出选项视图
struct ExportOptionsView: View {
    @Binding var options: ExportOptions
    @Binding var isPresented: Bool

    let onExport: (ExportOptions) -> Void

    var body: some View {
        VStack(spacing: 20) {
            // 标题
            headerView

            Divider()

            // 导出格式
            formatSection

            Divider()

            // 布局选项
            layoutSection

            Divider()

            // 其他选项
            optionsSection

            Spacer()

            // 操作按钮
            actionButtons
        }
        .padding(24)
        .frame(width: 500, height: 550)
    }

    // MARK: - Header

    private var headerView: some View {
        HStack(spacing: 12) {
            Image(systemName: "square.and.arrow.up")
                .font(.system(size: 28))
                .foregroundColor(.blue)

            VStack(alignment: .leading, spacing: 4) {
                Text("导出翻译结果")
                    .font(.title2)
                    .fontWeight(.semibold)

                Text("选择导出格式和布局选项")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()
        }
    }

    // MARK: - Format Section

    private var formatSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("导出格式")
                .font(.headline)

            ForEach(ExportFormat.allCases) { format in
                FormatOptionRow(
                    format: format,
                    isSelected: options.format == format,
                    onSelect: {
                        options.format = format
                    }
                )
            }
        }
    }

    // MARK: - Layout Section

    private var layoutSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("布局方式")
                .font(.headline)

            ForEach(ExportLayout.allCases) { layout in
                LayoutOptionRow(
                    layout: layout,
                    isSelected: options.layout == layout,
                    onSelect: {
                        options.layout = layout
                    }
                )
            }
        }
    }

    // MARK: - Options Section

    private var optionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("附加选项")
                .font(.headline)

            Toggle(isOn: $options.includeMetadata) {
                HStack(spacing: 8) {
                    Image(systemName: "info.circle")
                        .foregroundColor(.blue)
                    Text("包含元数据（文件数量、导出时间）")
                        .font(.subheadline)
                }
            }

            Toggle(isOn: $options.includeTimestamp) {
                HStack(spacing: 8) {
                    Image(systemName: "clock")
                        .foregroundColor(.orange)
                    Text("包含时间戳")
                        .font(.subheadline)
                }
            }
            .disabled(!options.includeMetadata)
        }
    }

    // MARK: - Action Buttons

    private var actionButtons: some View {
        HStack(spacing: 12) {
            Button("取消") {
                isPresented = false
            }
            .keyboardShortcut(.cancelAction)

            Spacer()

            Button(action: {
                onExport(options)
                isPresented = false
            }) {
                Label("导出", systemImage: "square.and.arrow.up")
            }
            .buttonStyle(.borderedProminent)
            .keyboardShortcut(.defaultAction)
        }
    }
}

// MARK: - Format Option Row

struct FormatOptionRow: View {
    let format: ExportFormat
    let isSelected: Bool
    let onSelect: () -> Void

    var body: some View {
        Button(action: onSelect) {
            HStack(spacing: 12) {
                // 选择指示器
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(isSelected ? .blue : .secondary)
                    .font(.system(size: 20))

                // 格式图标
                Image(systemName: format.icon)
                    .font(.system(size: 16))
                    .foregroundColor(.blue)
                    .frame(width: 24)

                // 格式信息
                VStack(alignment: .leading, spacing: 2) {
                    Text(format.displayName)
                        .font(.subheadline)
                        .fontWeight(.medium)

                    Text(formatDescription(format))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()
            }
            .padding(10)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(isSelected ? Color.blue.opacity(0.1) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isSelected ? Color.blue : Color.gray.opacity(0.3), lineWidth: 1.5)
            )
        }
        .buttonStyle(.plain)
    }

    private func formatDescription(_ format: ExportFormat) -> String {
        switch format {
        case .txt:
            return "纯文本格式，兼容性最好"
        case .pdf:
            return "PDF 文档，适合打印和分享"
        case .docx:
            return "Word 文档，可进一步编辑"
        }
    }
}

// MARK: - Layout Option Row

struct LayoutOptionRow: View {
    let layout: ExportLayout
    let isSelected: Bool
    let onSelect: () -> Void

    var body: some View {
        Button(action: onSelect) {
            HStack(spacing: 12) {
                // 选择指示器
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(isSelected ? .blue : .secondary)
                    .font(.system(size: 20))

                // 布局预览图标
                layoutPreview
                    .frame(width: 32, height: 24)

                // 布局信息
                VStack(alignment: .leading, spacing: 2) {
                    Text(layout.displayName)
                        .font(.subheadline)
                        .fontWeight(.medium)

                    Text(layout.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()
            }
            .padding(10)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(isSelected ? Color.blue.opacity(0.1) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isSelected ? Color.blue : Color.gray.opacity(0.3), lineWidth: 1.5)
            )
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private var layoutPreview: some View {
        switch layout {
        case .sourceOnly:
            Rectangle()
                .fill(Color.blue.opacity(0.3))

        case .translationOnly:
            Rectangle()
                .fill(Color.green.opacity(0.3))

        case .sideBySide:
            HStack(spacing: 2) {
                Rectangle()
                    .fill(Color.blue.opacity(0.3))
                Rectangle()
                    .fill(Color.green.opacity(0.3))
            }

        case .sequential:
            VStack(spacing: 2) {
                Rectangle()
                    .fill(Color.blue.opacity(0.3))
                Rectangle()
                    .fill(Color.green.opacity(0.3))
            }
        }
    }
}

// MARK: - Preview

#Preview {
    ExportOptionsView(
        options: .constant(.default),
        isPresented: .constant(true),
        onExport: { _ in }
    )
}
