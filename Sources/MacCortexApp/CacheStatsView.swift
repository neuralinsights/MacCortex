//
//  CacheStatsView.swift
//  MacCortex
//
//  Phase 3 Week 2 Day 5 - 缓存统计界面 UI
//  Created on 2026-01-22
//

import SwiftUI
import Charts

struct CacheStatsView: View {
    @StateObject private var viewModel = CacheStatsViewModel()

    var body: some View {
        VStack(spacing: 0) {
            // 顶部工具栏
            toolbarView
                .padding()
                .background(Color(NSColor.controlBackgroundColor))

            Divider()

            ScrollView {
                VStack(spacing: 20) {
                    // 缓存统计卡片
                    cacheStatsCard

                    // 性能统计卡片
                    performanceStatsCard

                    // 历史记录卡片
                    historyCard
                }
                .padding()
            }
        }
        .frame(minWidth: 600, minHeight: 500)
        .task {
            await viewModel.fetchCacheStats()
        }
    }

    // MARK: - 工具栏

    private var toolbarView: some View {
        HStack {
            Text("缓存统计")
                .font(.headline)

            Spacer()

            // 最后更新时间
            if let updateTime = viewModel.lastUpdateTime {
                Text("更新于 \(updateTime, style: .time)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            // 刷新按钮
            Button(action: {
                Task {
                    await viewModel.refresh()
                }
            }) {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 14))
            }
            .buttonStyle(.plain)
            .disabled(viewModel.isLoading)
            .help("刷新统计 (Cmd+R)")
            .keyboardShortcut("r", modifiers: .command)

            if viewModel.isLoading {
                ProgressView()
                    .scaleEffect(0.7)
            }
        }
    }

    // MARK: - 缓存统计卡片

    private var cacheStatsCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "tray.fill")
                    .foregroundColor(.blue)
                Text("缓存状态")
                    .font(.headline)

                Spacer()

                Button(action: {
                    Task {
                        await viewModel.clearCache()
                    }
                }) {
                    Label("清空缓存", systemImage: "trash")
                        .font(.caption)
                }
                .buttonStyle(.bordered)
            }

            Divider()

            // 缓存大小
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("缓存大小")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    HStack(alignment: .firstTextBaseline, spacing: 4) {
                        Text("\(viewModel.cacheSize)")
                            .font(.system(size: 32, weight: .bold))
                        Text("/ \(viewModel.maxSize)")
                            .font(.title3)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()

                // 缓存使用率
                CircularProgressView(
                    progress: Double(viewModel.cacheSize) / Double(viewModel.maxSize),
                    label: "\(Int(Double(viewModel.cacheSize) / Double(viewModel.maxSize) * 100))%"
                )
                .frame(width: 80, height: 80)
            }

            // 统计指标网格
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                StatCardView(
                    icon: "checkmark.circle.fill",
                    iconColor: .green,
                    title: "命中次数",
                    value: "\(viewModel.totalHits)"
                )

                StatCardView(
                    icon: "xmark.circle.fill",
                    iconColor: .orange,
                    title: "未命中次数",
                    value: "\(viewModel.totalMisses)"
                )

                StatCardView(
                    icon: "trash.circle.fill",
                    iconColor: .red,
                    title: "淘汰次数",
                    value: "\(viewModel.totalEvictions)"
                )
            }

            // TTL 信息
            HStack(spacing: 16) {
                Image(systemName: "clock.fill")
                    .foregroundColor(.blue)
                    .font(.caption)

                Text("缓存有效期:")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Text("\(viewModel.ttl / 60) 分钟 (\(viewModel.ttl) 秒)")
                    .font(.caption)
                    .fontWeight(.medium)
            }
            .padding(8)
            .background(Color.blue.opacity(0.1))
            .cornerRadius(6)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }

    // MARK: - 性能统计卡片

    private var performanceStatsCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "chart.bar.fill")
                    .foregroundColor(.green)
                Text("性能统计")
                    .font(.headline)
            }

            Divider()

            // 缓存命中率
            VStack(alignment: .leading, spacing: 8) {
                Text("缓存命中率")
                    .font(.caption)
                    .foregroundColor(.secondary)

                HStack {
                    Text("\(viewModel.hitRate, specifier: "%.1f")%")
                        .font(.system(size: 40, weight: .bold))
                        .foregroundColor(hitRateColor)

                    Spacer()

                    // 命中率指示器
                    VStack(alignment: .trailing, spacing: 4) {
                        Text(hitRateLabel)
                            .font(.caption)
                            .foregroundColor(hitRateColor)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(hitRateColor.opacity(0.2))
                            .cornerRadius(4)

                        Text("总请求: \(viewModel.totalHits + viewModel.totalMisses)")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }

                // 进度条
                ProgressView(value: viewModel.hitRate, total: 100)
                    .tint(hitRateColor)
            }

            Divider()

            // 节省时间
            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 4) {
                        Image(systemName: "bolt.fill")
                            .foregroundColor(.yellow)
                        Text("节省时间")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    Text(formattedTimeSaved)
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.green)
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    Text("等效于避免")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text("\(viewModel.totalHits) 次完整翻译")
                        .font(.caption)
                        .fontWeight(.medium)
                }
            }
            .padding()
            .background(Color.green.opacity(0.1))
            .cornerRadius(8)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }

    // MARK: - 历史记录卡片

    private var historyCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "clock.fill")
                    .foregroundColor(.purple)
                Text("翻译历史")
                    .font(.headline)

                Spacer()

                Button(action: {
                    viewModel.exportHistoryCSV()
                }) {
                    Label("导出 CSV", systemImage: "square.and.arrow.down")
                        .font(.caption)
                }
                .buttonStyle(.bordered)

                Button(action: {
                    viewModel.exportStatsJSON()
                }) {
                    Label("导出报告", systemImage: "doc.text")
                        .font(.caption)
                }
                .buttonStyle(.bordered)
            }

            Divider()

            if viewModel.translationHistory.isEmpty {
                // 空状态
                VStack(spacing: 12) {
                    Image(systemName: "clock.badge.xmark")
                        .font(.system(size: 40))
                        .foregroundColor(.secondary)
                    Text("暂无翻译历史")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 40)
            } else {
                // 历史记录列表
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(viewModel.translationHistory.prefix(20)) { item in
                            HistoryItemCard(item: item)
                        }
                    }
                }
                .frame(height: 300)
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }

    // MARK: - Computed Properties

    private var hitRateColor: Color {
        if viewModel.hitRate >= 70 {
            return .green
        } else if viewModel.hitRate >= 40 {
            return .orange
        } else {
            return .red
        }
    }

    private var hitRateLabel: String {
        if viewModel.hitRate >= 70 {
            return "优秀"
        } else if viewModel.hitRate >= 40 {
            return "良好"
        } else {
            return "较低"
        }
    }

    private var formattedTimeSaved: String {
        let seconds = viewModel.timeSaved
        if seconds < 60 {
            return String(format: "%.1f 秒", seconds)
        } else if seconds < 3600 {
            return String(format: "%.1f 分钟", seconds / 60)
        } else {
            return String(format: "%.1f 小时", seconds / 3600)
        }
    }
}

// MARK: - 统计卡片视图

struct StatCardView: View {
    let icon: String
    let iconColor: Color
    let title: String
    let value: String

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(iconColor)

            Text(value)
                .font(.title3)
                .fontWeight(.bold)

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(NSColor.windowBackgroundColor))
        .cornerRadius(8)
    }
}

// MARK: - 圆形进度视图

struct CircularProgressView: View {
    let progress: Double
    let label: String

    var body: some View {
        ZStack {
            Circle()
                .stroke(Color.gray.opacity(0.2), lineWidth: 8)

            Circle()
                .trim(from: 0, to: progress)
                .stroke(progressColor, style: StrokeStyle(lineWidth: 8, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut(duration: 0.5), value: progress)

            Text(label)
                .font(.headline)
                .fontWeight(.bold)
        }
    }

    private var progressColor: Color {
        if progress >= 0.7 {
            return .green
        } else if progress >= 0.4 {
            return .orange
        } else {
            return .red
        }
    }
}

// MARK: - 历史记录卡片

struct HistoryItemCard: View {
    let item: TranslationHistory

    var body: some View {
        HStack(spacing: 12) {
            // 时间和缓存状态
            VStack(alignment: .leading, spacing: 4) {
                Text(item.formattedTime)
                    .font(.caption2)
                    .foregroundColor(.secondary)

                if item.cached {
                    HStack(spacing: 2) {
                        Image(systemName: "bolt.fill")
                            .font(.system(size: 8))
                        Text("缓存")
                            .font(.caption2)
                    }
                    .foregroundColor(.green)
                }
            }
            .frame(width: 80)

            Divider()

            // 语言对
            HStack(spacing: 4) {
                Text(item.sourceLanguage.flag)
                Image(systemName: "arrow.right")
                    .font(.system(size: 8))
                    .foregroundColor(.secondary)
                Text(item.targetLanguage.flag)
            }
            .frame(width: 60)

            Divider()

            // 文本预览
            VStack(alignment: .leading, spacing: 2) {
                Text(item.sourcePreview)
                    .font(.caption)
                    .lineLimit(1)

                Text(item.translatedPreview)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            Divider()

            // 耗时
            Text("\(item.duration, specifier: "%.3f")s")
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 60, alignment: .trailing)
        }
        .padding(8)
        .background(Color(NSColor.windowBackgroundColor))
        .cornerRadius(6)
    }
}

// MARK: - 预览

#Preview {
    CacheStatsView()
        .frame(width: 800, height: 600)
}
