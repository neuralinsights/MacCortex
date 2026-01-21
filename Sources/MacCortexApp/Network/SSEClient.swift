//
//  SSEClient.swift
//  MacCortex
//
//  Phase 3 Week 3 Day 2 - Server-Sent Events (SSE) 客户端
//  Created on 2026-01-22
//

import Foundation

/// SSE 事件结构
struct SSEEvent {
    let event: String
    let data: String
}

/// Server-Sent Events 客户端
///
/// 用于接收 Backend 的流式翻译输出（/execute/stream）
/// 支持实时接收翻译片段，实现类似 ChatGPT 的打字效果
class SSEClient: NSObject, URLSessionDataDelegate {
    // MARK: - Properties

    private var session: URLSession!
    private var task: URLSessionDataTask?
    private var buffer = ""

    /// 接收到 SSE 事件时的回调
    var onEvent: ((SSEEvent) -> Void)?

    /// 连接完成时的回调
    var onComplete: (() -> Void)?

    /// 发生错误时的回调
    var onError: ((Error) -> Void)?

    // MARK: - Initialization

    override init() {
        super.init()

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 300  // 5 分钟超时
        config.timeoutIntervalForResource = 300
        config.httpAdditionalHeaders = [
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache"
        ]

        session = URLSession(configuration: config, delegate: self, delegateQueue: nil)
    }

    // MARK: - Public Methods

    /// 连接到 SSE 端点
    ///
    /// - Parameters:
    ///   - url: SSE 端点 URL（POST /execute/stream）
    ///   - body: 请求体（JSON 编码的 PatternRequest）
    func connect(url: URL, body: Data) {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.httpBody = body

        task = session.dataTask(with: request)
        task?.resume()
    }

    /// 断开连接
    func disconnect() {
        task?.cancel()
        task = nil
        buffer = ""
    }

    // MARK: - URLSessionDataDelegate

    /// 接收数据（流式接收）
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        guard let chunk = String(data: data, encoding: .utf8) else { return }

        buffer += chunk

        // 解析 SSE 事件（以双换行符 "\n\n" 分隔）
        let events = buffer.components(separatedBy: "\n\n")
        buffer = events.last ?? ""  // 保留最后一个不完整的事件

        // 处理所有完整的事件
        for eventString in events.dropLast() where !eventString.isEmpty {
            parseEvent(eventString)
        }
    }

    /// 请求完成
    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            DispatchQueue.main.async {
                self.onError?(error)
            }
        } else {
            DispatchQueue.main.async {
                self.onComplete?()
            }
        }
    }

    // MARK: - Private Methods

    /// 解析单个 SSE 事件
    ///
    /// SSE 格式：
    /// ```
    /// event: chunk
    /// data: {"text": "你好"}
    ///
    /// ```
    private func parseEvent(_ eventString: String) {
        var event = ""
        var data = ""

        for line in eventString.components(separatedBy: "\n") {
            if line.hasPrefix("event: ") {
                event = String(line.dropFirst(7))  // "event: ".count = 7
            } else if line.hasPrefix("data: ") {
                data = String(line.dropFirst(6))   // "data: ".count = 6
            }
        }

        if !event.isEmpty && !data.isEmpty {
            let sseEvent = SSEEvent(event: event, data: data)
            DispatchQueue.main.async {
                self.onEvent?(sseEvent)
            }
        }
    }

    deinit {
        disconnect()
    }
}
